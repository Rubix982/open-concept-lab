// Package kv is a key-value state machine on top of Raft. Every operation,
// reads included, goes through the log, so the store is linearizable: a read
// sees every write that finished before it began.
package kv

import (
	"bytes"
	"encoding/gob"
	"errors"
	"sync"
	"time"

	"raftkv/internal/raft"
)

// Op is one client operation as it travels through the log. ClientID and Seq
// make a retried operation apply once: a client retries on timeout, and the
// first attempt may have committed.
type Op struct {
	ClientID int64
	Seq      int64
	Kind     string // "get" or "put"
	Key      string
	Value    string
}

// Errors a client sees. ErrWrongLeader and ErrTimeout both mean "try elsewhere";
// after ErrTimeout the operation may or may not have happened.
var (
	ErrWrongLeader = errors.New("kv: not the leader")
	ErrTimeout     = errors.New("kv: no commit in time")
)

// Args and Reply are the client RPC, registered as "KV.Do".
type Args struct{ Op Op }

type Reply struct {
	Value  string
	Err    string // "" on success; else ErrWrongLeader's or ErrTimeout's text
	Leader int    // a hint: the leader this server last heard from, or -1
}

type result struct {
	clientID, seq int64
	value         string
}

// Server applies committed operations and answers clients.
type Server struct {
	node    *raft.Node
	timeout time.Duration

	mu      sync.Mutex
	data    map[string]string
	last    map[int64]result // per client, its latest applied operation
	waiters map[int]chan result
	applied int
}

// NewServer applies everything that arrives on apply, which must be the channel
// the node was configured with. A restarted server starts empty and the node
// replays its log into it.
func NewServer(node *raft.Node, apply <-chan raft.ApplyMsg, timeout time.Duration) *Server {
	s := &Server{
		node: node, timeout: timeout,
		data: map[string]string{}, last: map[int64]result{}, waiters: map[int]chan result{},
	}
	go s.run(apply)

	return s
}

func (s *Server) run(apply <-chan raft.ApplyMsg) {
	for m := range apply {
		s.mu.Lock()
		res, ok := s.applyCommand(m.Command)
		s.applied = m.Index
		if w := s.waiters[m.Index]; w != nil {
			delete(s.waiters, m.Index)
			if !ok {
				res = result{clientID: -1} // a leader's no-op took the slot
			}
			w <- res
		}
		s.mu.Unlock()
	}
}

// applyCommand runs one committed command, once per (client, seq).
func (s *Server) applyCommand(command []byte) (result, bool) {
	if len(command) == 0 {
		return result{}, false // a new leader's no-op
	}
	var op Op
	if err := gob.NewDecoder(bytes.NewReader(command)).Decode(&op); err != nil {
		return result{}, false
	}
	if prev, ok := s.last[op.ClientID]; ok && op.Seq <= prev.seq {
		// A duplicate: answer with what the original applied, if it is the latest.
		if op.Seq == prev.seq {
			return prev, true
		}
		return result{clientID: op.ClientID, seq: op.Seq}, true
	}
	res := result{clientID: op.ClientID, seq: op.Seq}
	switch op.Kind {
	case "put":
		s.data[op.Key] = op.Value
	case "get":
		res.value = s.data[op.Key]
	}
	s.last[op.ClientID] = res

	return res, true
}

// Do submits an operation and waits for it to commit and apply.
func (s *Server) Do(args *Args, reply *Reply) error {
	_, _, hint := s.node.Status()
	reply.Leader = hint
	var buf bytes.Buffer
	if err := gob.NewEncoder(&buf).Encode(args.Op); err != nil {
		return err
	}
	s.mu.Lock()
	index, _, isLeader := s.node.Start(buf.Bytes())
	if !isLeader {
		s.mu.Unlock()
		reply.Err = ErrWrongLeader.Error()
		return nil
	}
	wait := make(chan result, 1)
	s.waiters[index] = wait
	s.mu.Unlock()

	select {
	case res := <-wait:
		if res.clientID != args.Op.ClientID || res.seq != args.Op.Seq {
			// Another entry committed at our index: we lost leadership mid-way.
			reply.Err = ErrWrongLeader.Error()
			return nil
		}
		reply.Value = res.value
	case <-time.After(s.timeout):
		s.mu.Lock()
		if s.waiters[index] == wait {
			delete(s.waiters, index)
		}
		s.mu.Unlock()
		reply.Err = ErrTimeout.Error()
	}

	return nil
}
