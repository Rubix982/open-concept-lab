package faultnet

import (
	"bufio"
	"net"
	"testing"
	"time"
)

// echo serves one line back per line received.
func echo(t *testing.T) string {
	t.Helper()
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { l.Close() })
	go func() {
		for {
			c, err := l.Accept()
			if err != nil {
				return
			}
			go func() {
				r := bufio.NewReader(c)
				for {
					line, err := r.ReadString('\n')
					if err != nil {
						c.Close()
						return
					}
					c.Write([]byte(line))
				}
			}()
		}
	}()
	return l.Addr().String()
}

func roundTrip(c net.Conn) error {
	c.SetDeadline(time.Now().Add(500 * time.Millisecond))
	if _, err := c.Write([]byte("ping\n")); err != nil {
		return err
	}
	_, err := bufio.NewReader(c).ReadString('\n')
	return err
}

func TestCutDropsOpenConnectionsAndRefusesNewOnes(t *testing.T) {
	link, err := Listen(echo(t))
	if err != nil {
		t.Fatal(err)
	}
	defer link.Close()
	c, err := net.Dial("tcp", link.Addr())
	if err != nil {
		t.Fatal(err)
	}
	if err := roundTrip(c); err != nil {
		t.Fatalf("an up link failed: %v", err)
	}
	link.Cut()
	if err := roundTrip(c); err == nil {
		t.Fatal("an open connection survived a cut")
	}
	if c2, err := net.Dial("tcp", link.Addr()); err == nil {
		if roundTrip(c2) == nil {
			t.Fatal("a new connection got through a cut link")
		}
	}
	link.Heal()
	c3, err := net.Dial("tcp", link.Addr())
	if err != nil {
		t.Fatal(err)
	}
	if err := roundTrip(c3); err != nil {
		t.Fatalf("a healed link failed: %v", err)
	}
}

func TestPartitionCutsOnlyAcrossSides(t *testing.T) {
	addrs := []string{echo(t), echo(t), echo(t)}
	m, err := NewMesh(addrs)
	if err != nil {
		t.Fatal(err)
	}
	defer m.Close()
	m.Partition([]int{0})
	for i := range 3 {
		for j := range 3 {
			if i == j {
				continue
			}
			want := i == 0 || j == 0
			if got := m.links[i][j].IsCut(); got != want {
				t.Errorf("link %d->%d cut=%v, want %v", i, j, got, want)
			}
		}
	}
	m.HealAll()
	if m.links[0][1].IsCut() {
		t.Fatal("HealAll left a link cut")
	}
}
