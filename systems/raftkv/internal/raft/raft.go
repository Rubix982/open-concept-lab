// Package raft is a Raft consensus node: leader election, log replication and
// commitment, with term, vote and log persisted before they are acted on, so a
// restarted process recovers. It knows nothing of keys and values; the state
// machine above it does, through the apply channel.
//
// The rules followed are Figure 2 of Ongaro & Ousterhout, "In Search of an
// Understandable Consensus Algorithm" (2014), plus the conflict-term shortcut
// of §5.3 for backing up a lagging follower quickly.
package raft

import (
	"math/rand"
	"sync"
	"time"
)

// Entry is one command in the log, with the term it was received in.
type Entry struct {
	Term    int
	Command []byte
}

// ApplyMsg hands a committed command to the state machine, in log order.
type ApplyMsg struct {
	Index   int
	Term    int
	Command []byte
}

// RequestVoteArgs and the rest are the two RPCs of Figure 2.
type RequestVoteArgs struct {
	Term, Candidate, LastLogIndex, LastLogTerm int
}

type RequestVoteReply struct {
	Term    int
	Granted bool
}

type AppendEntriesArgs struct {
	Term, Leader, PrevLogIndex, PrevLogTerm, LeaderCommit int
	Entries                                               []Entry
}

// AppendEntriesReply carries the conflict hint: on a mismatch, the term of the
// follower's entry at PrevLogIndex and the first index it holds for that term,
// or, if its log is too short, its length.
type AppendEntriesReply struct {
	Term          int
	Success       bool
	ConflictTerm  int
	ConflictIndex int
}

// Transport carries RPCs to peer i. An error means no answer: lost, refused or late.
type Transport interface {
	RequestVote(peer int, args *RequestVoteArgs) (*RequestVoteReply, error)
	AppendEntries(peer int, args *AppendEntriesArgs) (*AppendEntriesReply, error)
}

// Config sets up one node of a cluster of Peers nodes, numbered from 0.
type Config struct {
	ID, Peers int
	Transport Transport
	Storage   Storage
	Apply     chan<- ApplyMsg
	// Heartbeat is the leader's idle interval; elections time out after a random
	// 3 to 6 heartbeats without hearing from a leader.
	Heartbeat time.Duration
	Seed      int64
}

type role int

const (
	follower role = iota
	candidate
	leader
)

// Node is one Raft server.
type Node struct {
	mu   sync.Mutex
	cfg  Config
	rng  *rand.Rand
	kick chan struct{} // wakes the replicator early: a new command arrived

	// Persistent state, saved before any reply or send that depends on it.
	term     int
	votedFor int     // -1 for none
	log      []Entry // log[0] is a sentinel with term 0, so real entries start at 1

	// Volatile state.
	role        role
	leaderID    int
	commitIndex int
	lastApplied int
	deadline    time.Time // when a follower or candidate starts an election
	nextIndex   []int
	matchIndex  []int
	inflight    []bool // one AppendEntries per peer at a time
	applyCond   *sync.Cond
	stopped     bool
	stopOnce    sync.Once
	done        chan struct{}
	wg          sync.WaitGroup
}

// New starts a node from whatever its storage holds.
func New(cfg Config) (*Node, error) {
	if cfg.Heartbeat == 0 {
		cfg.Heartbeat = 50 * time.Millisecond
	}
	n := &Node{
		cfg:      cfg,
		rng:      rand.New(rand.NewSource(cfg.Seed + int64(cfg.ID)*7919)),
		kick:     make(chan struct{}, 1),
		votedFor: -1,
		log:      []Entry{{Term: 0}},
		leaderID: -1,
		done:     make(chan struct{}),
	}
	n.applyCond = sync.NewCond(&n.mu)
	st, ok, err := cfg.Storage.Load()
	if err != nil {
		return nil, err
	}
	if ok {
		n.term, n.votedFor, n.log = st.Term, st.VotedFor, st.Log
	}
	n.resetDeadline()
	n.wg.Add(3)
	go n.ticker()
	go n.replicator()
	go n.applier()

	return n, nil
}

// Stop ends the node's goroutines; a second call does nothing. The apply
// channel is not closed.
func (n *Node) Stop() {
	n.stopOnce.Do(func() {
		n.mu.Lock()
		n.stopped = true
		n.applyCond.Broadcast()
		n.mu.Unlock()
		close(n.done)
		n.wg.Wait()
	})
}

// Start proposes a command. It returns at once; the command is applied only if
// it commits at the returned index in the returned term.
func (n *Node) Start(command []byte) (index, term int, isLeader bool) {
	n.mu.Lock()
	defer n.mu.Unlock()
	if n.role != leader || n.stopped {
		return 0, n.term, false
	}
	n.log = append(n.log, Entry{Term: n.term, Command: command})
	n.persist()
	n.matchIndex[n.cfg.ID] = n.lastIndex()
	select {
	case n.kick <- struct{}{}:
	default:
	}

	return n.lastIndex(), n.term, true
}

// Status reports the node's term, whether it believes it leads, and the leader
// it last heard from (-1 if none).
func (n *Node) Status() (term int, isLeader bool, leaderID int) {
	n.mu.Lock()
	defer n.mu.Unlock()

	return n.term, n.role == leader, n.leaderID
}

func (n *Node) lastIndex() int { return len(n.log) - 1 }
func (n *Node) lastTerm() int  { return n.log[len(n.log)-1].Term }

func (n *Node) persist() {
	// A node that cannot persist must not act on unsaved state: crash, as a disk
	// failure would, and let the restart recover from the last save.
	if err := n.cfg.Storage.Save(State{Term: n.term, VotedFor: n.votedFor, Log: n.log}); err != nil {
		panic("raft: persist: " + err.Error())
	}
}

func (n *Node) resetDeadline() {
	hb := n.cfg.Heartbeat
	n.deadline = time.Now().Add(3*hb + time.Duration(n.rng.Int63n(int64(3*hb))))
}

// stepDown moves to a newer term as a follower. Caller holds mu and persists.
func (n *Node) stepDown(term int) {
	n.term = term
	n.votedFor = -1
	n.role = follower
}

// ------------------------------------------------------------------ election

func (n *Node) ticker() {
	defer n.wg.Done()
	t := time.NewTicker(n.cfg.Heartbeat / 5)
	defer t.Stop()
	for {
		select {
		case <-n.done:
			return
		case <-t.C:
		}
		n.mu.Lock()
		if n.role != leader && time.Now().After(n.deadline) {
			n.startElection()
		}
		n.mu.Unlock()
	}
}

// startElection runs with mu held; votes are gathered by goroutines.
func (n *Node) startElection() {
	n.term++
	n.role = candidate
	n.votedFor = n.cfg.ID
	n.leaderID = -1
	n.persist()
	n.resetDeadline()
	args := &RequestVoteArgs{Term: n.term, Candidate: n.cfg.ID, LastLogIndex: n.lastIndex(), LastLogTerm: n.lastTerm()}
	votes := 1
	for p := 0; p < n.cfg.Peers; p++ {
		if p == n.cfg.ID {
			continue
		}
		go func(p int) {
			reply, err := n.cfg.Transport.RequestVote(p, args)
			if err != nil {
				return
			}
			n.mu.Lock()
			defer n.mu.Unlock()
			if reply.Term > n.term {
				n.stepDown(reply.Term)
				n.persist()
				return
			}
			if n.role != candidate || n.term != args.Term || !reply.Granted {
				return
			}
			votes++
			if votes > n.cfg.Peers/2 {
				n.becomeLeader()
			}
		}(p)
	}
}

func (n *Node) becomeLeader() {
	n.role = leader
	n.leaderID = n.cfg.ID
	n.nextIndex = make([]int, n.cfg.Peers)
	n.matchIndex = make([]int, n.cfg.Peers)
	n.inflight = make([]bool, n.cfg.Peers)
	for p := range n.nextIndex {
		n.nextIndex[p] = n.lastIndex() + 1
	}
	n.matchIndex[n.cfg.ID] = n.lastIndex()
	// A leader commits entries of earlier terms only by committing one of its own:
	// append a no-op so a quiet cluster still learns what is committed (§8).
	n.log = append(n.log, Entry{Term: n.term})
	n.persist()
	n.matchIndex[n.cfg.ID] = n.lastIndex()
	select {
	case n.kick <- struct{}{}:
	default:
	}
}

// HandleRequestVote answers a candidate (Figure 2, RequestVote receiver).
func (n *Node) HandleRequestVote(args *RequestVoteArgs) *RequestVoteReply {
	n.mu.Lock()
	defer n.mu.Unlock()
	if args.Term > n.term {
		n.stepDown(args.Term)
	}
	upToDate := args.LastLogTerm > n.lastTerm() ||
		(args.LastLogTerm == n.lastTerm() && args.LastLogIndex >= n.lastIndex())
	granted := args.Term == n.term && (n.votedFor == -1 || n.votedFor == args.Candidate) && upToDate
	if granted {
		n.votedFor = args.Candidate
		n.resetDeadline()
	}
	n.persist()

	return &RequestVoteReply{Term: n.term, Granted: granted}
}

// --------------------------------------------------------------- replication

func (n *Node) replicator() {
	defer n.wg.Done()
	t := time.NewTicker(n.cfg.Heartbeat)
	defer t.Stop()
	for {
		select {
		case <-n.done:
			return
		case <-t.C:
		case <-n.kick:
		}
		n.mu.Lock()
		if n.role == leader {
			for p := 0; p < n.cfg.Peers; p++ {
				if p != n.cfg.ID && !n.inflight[p] {
					n.inflight[p] = true
					go n.sendAppend(p, n.term)
				}
			}
		}
		n.mu.Unlock()
	}
}

func (n *Node) sendAppend(p, term int) {
	n.mu.Lock()
	if n.role != leader || n.term != term {
		n.inflight[p] = false
		n.mu.Unlock()
		return
	}
	prev := n.nextIndex[p] - 1
	entries := append([]Entry(nil), n.log[prev+1:]...)
	args := &AppendEntriesArgs{
		Term: n.term, Leader: n.cfg.ID, PrevLogIndex: prev, PrevLogTerm: n.log[prev].Term,
		LeaderCommit: n.commitIndex, Entries: entries,
	}
	n.mu.Unlock()

	reply, err := n.cfg.Transport.AppendEntries(p, args)

	n.mu.Lock()
	defer n.mu.Unlock()
	if n.inflight != nil && n.term == term {
		n.inflight[p] = false
	}
	if err != nil {
		return
	}
	if reply.Term > n.term {
		n.stepDown(reply.Term)
		n.persist()
		return
	}
	if n.role != leader || n.term != term {
		return
	}
	if reply.Success {
		if m := prev + len(entries); m > n.matchIndex[p] {
			n.matchIndex[p] = m
			n.nextIndex[p] = m + 1
			n.advanceCommit()
		}
		return
	}
	// Back up past the conflict: to the end of our entries for ConflictTerm, if we
	// have any, else to where the follower's entries for that term begin.
	next := reply.ConflictIndex
	if reply.ConflictTerm > 0 {
		for i := n.lastIndex(); i > 0; i-- {
			if n.log[i].Term == reply.ConflictTerm {
				next = i + 1
				break
			}
		}
	}
	n.nextIndex[p] = max(1, min(next, n.lastIndex()+1))
	select {
	case n.kick <- struct{}{}:
	default:
	}
}

// advanceCommit commits the highest index a majority holds, if it is from the
// current term (Figure 8: an older term's entry is never committed by counting).
func (n *Node) advanceCommit() {
	for i := n.lastIndex(); i > n.commitIndex; i-- {
		if n.log[i].Term != n.term {
			break
		}
		count := 0
		for p := 0; p < n.cfg.Peers; p++ {
			if n.matchIndex[p] >= i {
				count++
			}
		}
		if count > n.cfg.Peers/2 {
			n.commitIndex = i
			n.applyCond.Broadcast()
			return
		}
	}
}

// HandleAppendEntries answers a leader (Figure 2, AppendEntries receiver).
func (n *Node) HandleAppendEntries(args *AppendEntriesArgs) *AppendEntriesReply {
	n.mu.Lock()
	defer n.mu.Unlock()
	if args.Term < n.term {
		return &AppendEntriesReply{Term: n.term}
	}
	if args.Term > n.term || n.role != follower {
		n.stepDown(args.Term)
		if args.Term == n.term {
			n.votedFor = args.Leader
		}
		n.persist()
	}
	n.leaderID = args.Leader
	n.resetDeadline()

	if args.PrevLogIndex > n.lastIndex() {
		return &AppendEntriesReply{Term: n.term, ConflictIndex: n.lastIndex() + 1}
	}
	if t := n.log[args.PrevLogIndex].Term; t != args.PrevLogTerm {
		first := args.PrevLogIndex
		for first > 1 && n.log[first-1].Term == t {
			first--
		}
		return &AppendEntriesReply{Term: n.term, ConflictTerm: t, ConflictIndex: first}
	}
	// Append, truncating only at a real conflict: a delayed, shorter request must
	// not cut entries a later request already added.
	changed := false
	for i, e := range args.Entries {
		at := args.PrevLogIndex + 1 + i
		if at <= n.lastIndex() {
			if n.log[at].Term == e.Term {
				continue
			}
			n.log = n.log[:at]
		}
		n.log = append(n.log, args.Entries[i:]...)
		changed = true
		break
	}
	if changed {
		n.persist()
	}
	// Commit only what this request vouched for: entries past it may be stale.
	if c := min(args.LeaderCommit, args.PrevLogIndex+len(args.Entries)); c > n.commitIndex {
		n.commitIndex = c
		n.applyCond.Broadcast()
	}

	return &AppendEntriesReply{Term: n.term, Success: true}
}

// ------------------------------------------------------------------- apply

func (n *Node) applier() {
	defer n.wg.Done()
	n.mu.Lock()
	defer n.mu.Unlock()
	for {
		for !n.stopped && n.lastApplied >= n.commitIndex {
			n.applyCond.Wait()
		}
		if n.stopped {
			return
		}
		batch := make([]ApplyMsg, 0, n.commitIndex-n.lastApplied)
		for i := n.lastApplied + 1; i <= n.commitIndex; i++ {
			batch = append(batch, ApplyMsg{Index: i, Term: n.log[i].Term, Command: n.log[i].Command})
		}
		n.lastApplied = n.commitIndex
		n.mu.Unlock()
		for _, m := range batch {
			select {
			case n.cfg.Apply <- m:
			case <-n.done:
				n.mu.Lock()
				return
			}
		}
		n.mu.Lock()
	}
}
