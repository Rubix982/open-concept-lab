package raft

import (
	"fmt"
	"path/filepath"
	"testing"
	"time"
)

func TestElectsOneLeader(t *testing.T) {
	c := newCluster(t, 5)
	first := c.leader()
	time.Sleep(300 * time.Millisecond) // a quiet cluster keeps its leader
	if again := c.leader(); again != first {
		t.Fatalf("leader changed from %d to %d with no faults", first, again)
	}
}

func TestReelectsWhenLeaderIsCutOff(t *testing.T) {
	c := newCluster(t, 5)
	old := c.leader()
	c.isolate(old)
	if next := c.leader(old); next == old {
		t.Fatal("the cut-off leader is still the only leader")
	}
	c.heal()
	c.leader()
}

func TestCommitsNeedAMajority(t *testing.T) {
	c := newCluster(t, 5)
	c.submit("a", 5)
	l := c.leader()
	// Leave the leader with one follower: two of five cannot commit.
	minority := []int{l, (l + 1) % 5}
	for p := range 5 {
		if p != minority[0] && p != minority[1] {
			c.isolate(p)
		}
	}
	index, _, ok := c.net.nodes[l].Start([]byte("lost"))
	if !ok {
		t.Fatal("leader refused a command")
	}
	time.Sleep(400 * time.Millisecond)
	if got := c.countApplied(index, "lost"); got != 0 {
		t.Fatalf("a minority committed: %q applied on %d nodes", "lost", got)
	}
	c.heal()
	c.submit("after", 5)
	c.checkAgreement()
}

func TestMinorityLeaderLosesItsEntries(t *testing.T) {
	c := newCluster(t, 5)
	c.submit("base", 5)
	old := c.leader()
	c.isolate(old)
	c.net.nodes[old].Start([]byte("stale-1"))
	c.net.nodes[old].Start([]byte("stale-2"))
	next := c.leader(old)
	c.net.mu.Lock()
	c.net.cut = map[[2]int]bool{}
	for p := range 5 { // old leader stays cut while the majority moves on
		if p != old {
			c.net.cut[[2]int{old, p}], c.net.cut[[2]int{p, old}] = true, true
		}
	}
	c.net.mu.Unlock()
	_ = next
	for i := range 5 {
		c.submit(fmt.Sprintf("new-%d", i), 4)
	}
	c.heal()
	c.submit("final", 5)
	c.checkAgreement()
	if c.countApplied(2, "stale-1") != 0 {
		t.Fatal("an uncommitted entry from a deposed leader was applied")
	}
}

func TestRestartRecoversFromStorage(t *testing.T) {
	c := newCluster(t, 3)
	for i := range 10 {
		c.submit(fmt.Sprintf("x%d", i), 3)
	}
	for i := range 3 {
		c.crash(i)
	}
	for i := range 3 {
		c.start(i)
	}
	c.submit("after-restart", 3)
	c.checkAgreement()
	c.amu.Lock()
	defer c.amu.Unlock()
	for i, log := range c.applied {
		if len(log) < 11 {
			t.Fatalf("node %d replayed %d entries after restart, want at least 11", i, len(log))
		}
	}
}

func TestChurnKeepsAgreement(t *testing.T) {
	c := newCluster(t, 5)
	for round := range 12 {
		victim := round % 5
		if round%3 == 0 {
			c.crash(victim)
			c.submit(fmt.Sprintf("r%d", round), 3)
			c.start(victim)
		} else {
			c.isolate(victim)
			c.submit(fmt.Sprintf("r%d", round), 3)
			c.heal()
		}
	}
	c.submit("end", 5)
	c.checkAgreement()
}

func TestFileStorageRoundTrip(t *testing.T) {
	s := FileStorage{Path: filepath.Join(t.TempDir(), "state")}
	if _, ok, err := s.Load(); ok || err != nil {
		t.Fatalf("empty storage: ok=%v err=%v", ok, err)
	}
	want := State{Term: 7, VotedFor: 2, Log: []Entry{{}, {Term: 3, Command: []byte("put")}}}
	if err := s.Save(want); err != nil {
		t.Fatal(err)
	}
	got, ok, err := s.Load()
	if err != nil || !ok || got.Term != 7 || got.VotedFor != 2 || len(got.Log) != 2 || string(got.Log[1].Command) != "put" {
		t.Fatalf("got %+v ok=%v err=%v", got, ok, err)
	}
}
