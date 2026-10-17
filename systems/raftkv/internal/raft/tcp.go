package raft

import (
	"errors"
	"net"
	"net/rpc"
	"sync"
	"time"
)

// RPCService exposes a Node's two handlers to net/rpc, registered as "Raft".
type RPCService struct{ Node *Node }

func (s *RPCService) RequestVote(args *RequestVoteArgs, reply *RequestVoteReply) error {
	*reply = *s.Node.HandleRequestVote(args)
	return nil
}

func (s *RPCService) AppendEntries(args *AppendEntriesArgs, reply *AppendEntriesReply) error {
	*reply = *s.Node.HandleAppendEntries(args)
	return nil
}

// ErrTimeout is an RPC that got no answer in time.
var ErrTimeout = errors.New("raft: rpc timed out")

// TCPTransport reaches peers over TCP, one lazily dialled connection each,
// dropped and redialled after any failure. Every call has a deadline: a peer
// behind a cut link must cost a timeout, never a hang.
type TCPTransport struct {
	Addrs   []string
	Timeout time.Duration

	mu      sync.Mutex
	clients map[int]*rpc.Client
}

func NewTCPTransport(addrs []string, timeout time.Duration) *TCPTransport {
	return &TCPTransport{Addrs: addrs, Timeout: timeout, clients: map[int]*rpc.Client{}}
}

func (t *TCPTransport) client(peer int) (*rpc.Client, error) {
	t.mu.Lock()
	c := t.clients[peer]
	t.mu.Unlock()
	if c != nil {
		return c, nil
	}
	conn, err := net.DialTimeout("tcp", t.Addrs[peer], t.Timeout)
	if err != nil {
		return nil, err
	}
	c = rpc.NewClient(conn)
	t.mu.Lock()
	if old := t.clients[peer]; old != nil {
		t.mu.Unlock()
		c.Close()
		return old, nil
	}
	t.clients[peer] = c
	t.mu.Unlock()

	return c, nil
}

func (t *TCPTransport) drop(peer int, c *rpc.Client) {
	t.mu.Lock()
	if t.clients[peer] == c {
		delete(t.clients, peer)
	}
	t.mu.Unlock()
	c.Close()
}

func (t *TCPTransport) call(peer int, method string, args, reply any) error {
	c, err := t.client(peer)
	if err != nil {
		return err
	}
	call := c.Go(method, args, reply, make(chan *rpc.Call, 1))
	timer := time.NewTimer(t.Timeout)
	defer timer.Stop()
	select {
	case done := <-call.Done:
		if done.Error != nil {
			t.drop(peer, c)
		}
		return done.Error
	case <-timer.C:
		// The connection may be wedged behind a cut link; start over next time.
		t.drop(peer, c)
		return ErrTimeout
	}
}

func (t *TCPTransport) RequestVote(peer int, args *RequestVoteArgs) (*RequestVoteReply, error) {
	var reply RequestVoteReply
	if err := t.call(peer, "Raft.RequestVote", args, &reply); err != nil {
		return nil, err
	}
	return &reply, nil
}

func (t *TCPTransport) AppendEntries(peer int, args *AppendEntriesArgs) (*AppendEntriesReply, error) {
	var reply AppendEntriesReply
	if err := t.call(peer, "Raft.AppendEntries", args, &reply); err != nil {
		return nil, err
	}
	return &reply, nil
}

// Close drops every connection.
func (t *TCPTransport) Close() {
	t.mu.Lock()
	defer t.mu.Unlock()
	for p, c := range t.clients {
		c.Close()
		delete(t.clients, p)
	}
}
