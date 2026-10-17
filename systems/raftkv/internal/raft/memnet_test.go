package raft

import (
	"errors"
	"sync"
	"testing"
	"time"
)

// memNet joins test nodes in one process, with links that can be cut. It is
// for unit tests only; the torture run uses real processes and real sockets.
type memNet struct {
	mu    sync.Mutex
	nodes []*Node
	cut   map[[2]int]bool
}

var errCut = errors.New("memnet: link cut")

type memTransport struct {
	net  *memNet
	from int
}

func (t memTransport) reach(peer int) (*Node, error) {
	t.net.mu.Lock()
	defer t.net.mu.Unlock()
	if t.net.cut[[2]int{t.from, peer}] || t.net.nodes[peer] == nil {
		return nil, errCut
	}
	return t.net.nodes[peer], nil
}

func (t memTransport) RequestVote(peer int, a *RequestVoteArgs) (*RequestVoteReply, error) {
	n, err := t.reach(peer)
	if err != nil {
		return nil, err
	}
	r := n.HandleRequestVote(a)
	if _, err := t.reach(peer); err != nil { // the reply crosses the link too
		return nil, err
	}
	return r, nil
}

func (t memTransport) AppendEntries(peer int, a *AppendEntriesArgs) (*AppendEntriesReply, error) {
	n, err := t.reach(peer)
	if err != nil {
		return nil, err
	}
	r := n.HandleAppendEntries(a)
	if _, err := t.reach(peer); err != nil {
		return nil, err
	}
	return r, nil
}

type cluster struct {
	t       *testing.T
	net     *memNet
	store   []*MemStorage
	applied [][]ApplyMsg
	amu     sync.Mutex
	stops   []chan struct{}
}

func newCluster(t *testing.T, size int) *cluster {
	c := &cluster{
		t:       t,
		net:     &memNet{nodes: make([]*Node, size), cut: map[[2]int]bool{}},
		store:   make([]*MemStorage, size),
		applied: make([][]ApplyMsg, size),
		stops:   make([]chan struct{}, size),
	}
	for i := range size {
		c.store[i] = &MemStorage{}
		c.start(i)
	}
	t.Cleanup(func() {
		for i := range size {
			c.crash(i)
		}
	})
	return c
}

// start boots node i from its storage, as a process restart would.
func (c *cluster) start(i int) {
	apply := make(chan ApplyMsg, 64)
	stop := make(chan struct{})
	n, err := New(Config{
		ID: i, Peers: len(c.store), Transport: memTransport{c.net, i},
		Storage: c.store[i], Apply: apply, Heartbeat: 20 * time.Millisecond, Seed: 1,
	})
	if err != nil {
		c.t.Fatal(err)
	}
	c.amu.Lock()
	c.applied[i] = nil // the state machine restarts empty and replays the log
	c.amu.Unlock()
	go func() {
		for {
			select {
			case m := <-apply:
				c.amu.Lock()
				c.applied[i] = append(c.applied[i], m)
				c.amu.Unlock()
			case <-stop:
				return
			}
		}
	}()
	c.net.mu.Lock()
	c.net.nodes[i] = n
	c.net.mu.Unlock()
	c.stops[i] = stop
}

func (c *cluster) crash(i int) {
	c.net.mu.Lock()
	n := c.net.nodes[i]
	c.net.nodes[i] = nil
	c.net.mu.Unlock()
	if n != nil {
		n.Stop()
		close(c.stops[i])
	}
}

// isolate cuts every link to and from the nodes in group, both ways.
func (c *cluster) isolate(group ...int) {
	c.net.mu.Lock()
	defer c.net.mu.Unlock()
	for _, g := range group {
		for p := range c.net.nodes {
			if p != g {
				c.net.cut[[2]int{g, p}] = true
				c.net.cut[[2]int{p, g}] = true
			}
		}
	}
}

func (c *cluster) heal() {
	c.net.mu.Lock()
	c.net.cut = map[[2]int]bool{}
	c.net.mu.Unlock()
}

// leader waits for exactly one leader in the highest term among reachable nodes.
func (c *cluster) leader(excluding ...int) int {
	skip := map[int]bool{}
	for _, e := range excluding {
		skip[e] = true
	}
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		byTerm := map[int][]int{}
		top := -1
		c.net.mu.Lock()
		nodes := append([]*Node(nil), c.net.nodes...)
		c.net.mu.Unlock()
		for i, n := range nodes {
			if n == nil || skip[i] {
				continue
			}
			if term, isLeader, _ := n.Status(); isLeader {
				byTerm[term] = append(byTerm[term], i)
				top = max(top, term)
			}
		}
		if top >= 0 {
			if len(byTerm[top]) > 1 {
				c.t.Fatalf("term %d has %d leaders: %v", top, len(byTerm[top]), byTerm[top])
			}
			return byTerm[top][0]
		}
		time.Sleep(20 * time.Millisecond)
	}
	c.t.Fatal("no leader elected within 3s")
	return -1
}

// submit proposes cmd through whoever leads, retrying until it is applied on
// at least want nodes, and returns its index.
func (c *cluster) submit(cmd string, want int) int {
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		c.net.mu.Lock()
		nodes := append([]*Node(nil), c.net.nodes...)
		c.net.mu.Unlock()
		for _, n := range nodes {
			if n == nil {
				continue
			}
			index, _, ok := n.Start([]byte(cmd))
			if !ok {
				continue
			}
			for wait := time.Now().Add(time.Second); time.Now().Before(wait); time.Sleep(10 * time.Millisecond) {
				if got := c.countApplied(index, cmd); got >= want {
					return index
				}
			}
		}
		time.Sleep(20 * time.Millisecond)
	}
	c.t.Fatalf("%q never applied on %d nodes", cmd, want)
	return -1
}

func (c *cluster) countApplied(index int, cmd string) int {
	c.amu.Lock()
	defer c.amu.Unlock()
	count := 0
	for _, log := range c.applied {
		for _, m := range log {
			if m.Index == index && string(m.Command) == cmd {
				count++
			}
		}
	}
	return count
}

// checkAgreement fails if two nodes applied different commands at one index,
// or a node applied out of order: the State Machine Safety property.
func (c *cluster) checkAgreement() {
	c.amu.Lock()
	defer c.amu.Unlock()
	at := map[int]string{}
	for i, log := range c.applied {
		for k, m := range log {
			if m.Index != k+1 {
				c.t.Fatalf("node %d applied index %d in position %d", i, m.Index, k+1)
			}
			if prev, ok := at[m.Index]; ok && prev != string(m.Command) {
				c.t.Fatalf("index %d: %q on one node, %q on node %d", m.Index, prev, m.Command, i)
			}
			at[m.Index] = string(m.Command)
		}
	}
}
