package kv

import (
	"fmt"
	"net"
	"net/rpc"
	"testing"
	"time"

	"raftkv/internal/raft"
)

// tcpCluster runs n nodes in this process, each with its own TCP listener, so
// the transport and the client RPC are exercised over real sockets.
type tcpCluster struct {
	addrs     []string
	listeners []net.Listener
	nodes     []*raft.Node
	servers   []*Server
}

func newTCPCluster(t *testing.T, n int) *tcpCluster {
	t.Helper()
	c := &tcpCluster{}
	for range n {
		l, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			t.Fatal(err)
		}
		c.listeners = append(c.listeners, l)
		c.addrs = append(c.addrs, l.Addr().String())
	}
	for i := range n {
		apply := make(chan raft.ApplyMsg, 256)
		node, err := raft.New(raft.Config{
			ID: i, Peers: n, Transport: raft.NewTCPTransport(c.addrs, 100*time.Millisecond),
			Storage: raft.FileStorage{Path: fmt.Sprintf("%s/node-%d", t.TempDir(), i)},
			Apply:   apply, Heartbeat: 30 * time.Millisecond, Seed: 1,
		})
		if err != nil {
			t.Fatal(err)
		}
		srv := NewServer(node, apply, time.Second)
		rs := rpc.NewServer()
		if err := rs.RegisterName("Raft", &raft.RPCService{Node: node}); err != nil {
			t.Fatal(err)
		}
		if err := rs.RegisterName("KV", srv); err != nil {
			t.Fatal(err)
		}
		go rs.Accept(c.listeners[i])
		c.nodes = append(c.nodes, node)
		c.servers = append(c.servers, srv)
	}
	t.Cleanup(func() {
		for i := range n {
			c.listeners[i].Close()
			c.nodes[i].Stop()
		}
	})
	return c
}

func TestPutThenGetOverTCP(t *testing.T) {
	c := newTCPCluster(t, 3)
	cl := NewClient(c.addrs, 1, 300*time.Millisecond, 5*time.Second)
	defer cl.Close()
	for i := range 20 {
		if err := cl.Put("k", fmt.Sprint(i)); err != nil {
			t.Fatalf("put %d: %v", i, err)
		}
		got, err := cl.Get("k")
		if err != nil || got != fmt.Sprint(i) {
			t.Fatalf("get after put %d: %q, %v", i, got, err)
		}
	}
}

func TestRetriedPutAppliesOnce(t *testing.T) {
	s := &Server{data: map[string]string{}, last: map[int64]result{}, waiters: map[int]chan result{}}
	encode := func(op Op) []byte { return mustEncode(t, op) }
	s.applyCommand(encode(Op{ClientID: 9, Seq: 1, Kind: "put", Key: "k", Value: "first"}))
	s.applyCommand(encode(Op{ClientID: 8, Seq: 1, Kind: "put", Key: "k", Value: "other"}))
	// Client 9's put is retried and commits a second time, after client 8's.
	s.applyCommand(encode(Op{ClientID: 9, Seq: 1, Kind: "put", Key: "k", Value: "first"}))
	if got := s.data["k"]; got != "other" {
		t.Fatalf("a retried put applied twice: k = %q, want %q", got, "other")
	}
}

func TestSurvivesLeaderLoss(t *testing.T) {
	c := newTCPCluster(t, 3)
	cl := NewClient(c.addrs, 2, 300*time.Millisecond, 5*time.Second)
	defer cl.Close()
	if err := cl.Put("k", "before"); err != nil {
		t.Fatal(err)
	}
	for i, n := range c.nodes {
		if _, isLeader, _ := n.Status(); isLeader {
			c.listeners[i].Close()
			n.Stop()
		}
	}
	if err := cl.Put("k", "after"); err != nil {
		t.Fatalf("put after leader loss: %v", err)
	}
	if got, err := cl.Get("k"); err != nil || got != "after" {
		t.Fatalf("get: %q, %v", got, err)
	}
}
