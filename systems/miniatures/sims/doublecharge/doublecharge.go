// Package doublecharge: an AI agent paying for things through a payment tool,
// over a network that sometimes loses messages, and what a retry does.
//
// The agent sends a charge request and waits. If no reply comes within its
// timeout, it can't tell which of three things happened:
//   - the request was lost on the way (nothing was charged);
//   - the reply was lost on the way back (the charge went through);
//   - the server is just slow (the charge is still being made).
//
// So it retries. Without protection, every retry that reaches the server is
// a new charge. The standard fix is an idempotency key: the agent sends the
// same unique key with every attempt for one task, and the server makes sure
// one key means one charge. How the server checks the key matters:
//   - check, then insert: look the key up, do the charge, then record the
//     key. A retry that arrives while the first attempt is still being
//     processed finds nothing recorded and charges again.
//   - claim atomically: record the key as "in progress" first, in one step.
//     A retry that arrives meanwhile waits for the first attempt's result.
//
// Every task has its own key, so tasks don't interact; each one is simulated
// on its own with explicit timestamps for every message.
package doublecharge

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand/v2"
	"strings"

	"miniatures/sims/registry"
)

// Params are what the page's controls change.
type Params struct {
	Policy  string  `json:"policy"`  // no-key | check-insert | atomic
	Tasks   int     `json:"tasks"`   // purchases the agent makes
	Loss    float64 `json:"loss"`    // chance each message (request or reply) is lost
	Slow    float64 `json:"slow"`    // chance the server takes a long time on an attempt
	Timeout float64 `json:"timeout"` // seconds the agent waits before retrying
	Tries   int     `json:"tries"`   // attempts before the agent gives up
	Gap     float64 `json:"gap"`     // seconds between task starts
	Price   float64 `json:"price"`   // dollars per purchase
	Seed    uint64  `json:"seed"`
}

// Defaults: a network that loses about one message in twelve and a server
// that is occasionally slower than the agent's patience.
func Defaults() Params {
	return Params{Policy: "atomic", Tasks: 500, Loss: 0.08, Slow: 0.06, Timeout: 1.0, Tries: 4, Gap: 0.1, Price: 20, Seed: 11}
}

// Policies in the order the page shows them.
var Policies = []struct{ Name, Label string }{
	{"no-key", "No idempotency key"},
	{"check-insert", "Key: check, then insert"},
	{"atomic", "Key: claimed atomically"},
}

// What the server did with one attempt.
const (
	KindLost     = "lost"     // the request never arrived
	KindCharge   = "charge"   // a new charge was made
	KindReplay   = "replay"   // key already done: the stored result was sent back
	KindWaited   = "waited"   // key in progress: waited for the first attempt, then sent its result
)

// Attempt is one try at a task. Times are absolute seconds; -1 means "didn't
// happen".
type Attempt struct {
	Send    float64 `json:"send"`
	Arrive  float64 `json:"arrive"`  // at the server (-1: request lost)
	Kind    string  `json:"kind"`    // lost | charge | replay | waited
	Done    float64 `json:"done"`    // server finished and replied (-1 if never arrived)
	Charged bool    `json:"charged"` // this attempt made a charge
	Reply   float64 `json:"reply"`   // reply reached the agent (-1: lost, or never sent)
	Slow    bool    `json:"slow"`    // the server was slow on this one
}

// Task is one purchase.
type Task struct {
	ID       int       `json:"id"`
	Start    float64   `json:"start"`
	Attempts []Attempt `json:"att"`
	Charges  int       `json:"charges"`
	Finished float64   `json:"fin"`    // agent saw a reply (-1: gave up)
	GaveUp   float64   `json:"gaveUp"` // when it gave up (-1: didn't)
}

// Stats summarise one policy's run.
type Stats struct {
	Policy       string  `json:"policy"`
	Label        string  `json:"label"`
	Once         int     `json:"once"`         // charged exactly once
	Twice        int     `json:"twice"`        // charged two or more times
	Never        int     `json:"never"`        // never charged
	Extra        int     `json:"extra"`        // charges beyond one per task
	ExtraDollars float64 `json:"extraDollars"` // money taken that shouldn't have been
	GaveUp       int     `json:"gaveUp"`       // agent gave up waiting
	GaveUpPaid   int     `json:"gaveUpPaid"`   // ...though the customer was charged
	Attempts     float64 `json:"attempts"`     // average attempts per task
	Retried      int     `json:"retried"`      // tasks that needed more than one attempt
}

// Result is what the page gets.
type Result struct {
	Params Params  `json:"params"`
	Trace  []Task  `json:"trace"`
	End    float64 `json:"end"`
	Stats  []Stats `json:"stats"`
}

// fate is everything random about one attempt, drawn up front so every policy
// faces exactly the same network and server.
type fate struct {
	reqLost, repLost bool
	out, back, proc  float64
	slow             bool
}

func fates(p Params) [][]fate {
	r := rand.New(rand.NewPCG(p.Seed, 5))
	all := make([][]fate, p.Tasks)
	for i := range all {
		all[i] = make([]fate, p.Tries)
		for k := range all[i] {
			f := fate{
				reqLost: r.Float64() < p.Loss,
				repLost: r.Float64() < p.Loss,
				out:     0.05 + 0.1*r.Float64(),
				back:    0.05 + 0.1*r.Float64(),
				proc:    0.1 + 0.2*r.Float64(),
			}
			if r.Float64() < p.Slow {
				f.slow = true
				f.proc = 1.2 + 2.3*r.Float64() // longer than a typical timeout
			}
			all[i][k] = f
		}
	}
	return all
}

// task plays one purchase through: attempts go out one timeout apart until a
// reply comes back or the agent runs out of tries. Arrivals are in send order
// (the timeout is longer than the spread in network delay), so the server
// sees attempts in the order they were sent.
func task(p Params, id int, fs []fate) Task {
	t := Task{ID: id, Start: float64(id) * p.Gap, Finished: -1, GaveUp: -1}
	firstReply := math.Inf(1)
	// the server's record of this task's key
	claimed, committed := false, false
	commitAt := math.Inf(1)
	for k := 0; k < p.Tries; k++ {
		send := t.Start + float64(k)*p.Timeout
		if firstReply <= send {
			break // a reply already came back; no retry
		}
		f := fs[k]
		a := Attempt{Send: send, Arrive: -1, Done: -1, Reply: -1, Slow: f.slow}
		if f.reqLost {
			a.Kind = KindLost
		} else {
			a.Arrive = send + f.out
			switch p.Policy {
			case "no-key":
				a.Kind, a.Charged, a.Done = KindCharge, true, a.Arrive+f.proc
			case "check-insert":
				// the lookup only sees keys whose charge has finished
				if committed && commitAt <= a.Arrive {
					a.Kind, a.Done = KindReplay, a.Arrive+0.02
				} else {
					a.Kind, a.Charged, a.Done = KindCharge, true, a.Arrive+f.proc
					committed = true
					commitAt = math.Min(commitAt, a.Done)
				}
			case "atomic":
				switch {
				case !claimed:
					claimed = true
					a.Kind, a.Charged, a.Done = KindCharge, true, a.Arrive+f.proc
					commitAt = a.Done
				case commitAt > a.Arrive:
					a.Kind, a.Done = KindWaited, commitAt // waits for the first attempt
				default:
					a.Kind, a.Done = KindReplay, a.Arrive+0.02
				}
			}
			if a.Charged {
				t.Charges++
			}
			if !f.repLost {
				a.Reply = a.Done + f.back
				firstReply = math.Min(firstReply, a.Reply)
			}
		}
		t.Attempts = append(t.Attempts, a)
	}
	giveUp := t.Start + float64(len(t.Attempts))*p.Timeout
	if len(t.Attempts) < p.Tries {
		giveUp = math.Inf(1) // stopped early because a reply came
	}
	if firstReply <= giveUp {
		t.Finished = firstReply
	} else {
		t.GaveUp = giveUp
	}
	return t
}

// Simulate runs one policy.
func Simulate(p Params) (Result, error) {
	if p.Tasks < 1 || p.Tasks > 5000 || p.Loss < 0 || p.Loss > 0.9 || p.Slow < 0 || p.Slow > 1 ||
		p.Timeout < 0.3 || p.Timeout > 10 || p.Tries < 1 || p.Tries > 10 || p.Gap <= 0 || p.Gap > 10 {
		return Result{}, fmt.Errorf("parameters out of range")
	}
	ok := false
	for _, pol := range Policies {
		ok = ok || pol.Name == p.Policy
	}
	if !ok {
		return Result{}, fmt.Errorf("unknown policy %q", p.Policy)
	}
	fs := fates(p)
	res := Result{Params: p, Trace: make([]Task, p.Tasks)}
	for i := range res.Trace {
		t := task(p, i, fs[i])
		res.Trace[i] = t
		for _, a := range t.Attempts {
			res.End = math.Max(res.End, math.Max(a.Done, a.Reply))
		}
		res.End = math.Max(res.End, math.Max(t.Finished, t.GaveUp))
	}
	res.Stats = []Stats{stats(p, res.Trace)}
	return res, nil
}

func stats(p Params, trace []Task) Stats {
	st := Stats{Policy: p.Policy}
	for _, pol := range Policies {
		if pol.Name == p.Policy {
			st.Label = pol.Label
		}
	}
	var att int
	for _, t := range trace {
		att += len(t.Attempts)
		if len(t.Attempts) > 1 {
			st.Retried++
		}
		switch {
		case t.Charges == 0:
			st.Never++
		case t.Charges == 1:
			st.Once++
		default:
			st.Twice++
			st.Extra += t.Charges - 1
		}
		if t.GaveUp >= 0 {
			st.GaveUp++
			if t.Charges > 0 {
				st.GaveUpPaid++
			}
		}
	}
	st.ExtraDollars = float64(st.Extra) * p.Price
	st.Attempts = float64(att) / float64(len(trace))
	return st
}

// Run is the page's entry: the chosen policy's trace, plus every policy's
// numbers on the same network for the comparison table.
func Run(params json.RawMessage) (any, error) {
	p := Defaults()
	if err := registry.Decode(params, &p); err != nil {
		return nil, err
	}
	res, err := Simulate(p)
	if err != nil {
		return nil, err
	}
	res.Stats = nil
	for _, pol := range Policies {
		q := p
		q.Policy = pol.Name
		r, err := Simulate(q)
		if err != nil {
			return nil, err
		}
		res.Stats = append(res.Stats, r.Stats[0])
	}
	return res, nil
}

// Report is the terminal table.
func Report() string {
	out, _ := Run(nil)
	res := out.(Result)
	p := res.Params
	var b strings.Builder
	fmt.Fprintf(&b, "%d purchases at $%.0f, %.0f%% of messages lost, server slow %.0f%% of the time, timeout %.1fs, up to %d tries\n\n",
		p.Tasks, p.Price, p.Loss*100, p.Slow*100, p.Timeout, p.Tries)
	fmt.Fprintf(&b, "%-26s %6s %8s %7s %10s %8s %9s\n", "policy", "once", "twice+", "never", "extra $", "gave up", "attempts")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-26s %6d %8d %7d %10.0f %8d %9.2f\n", s.Label, s.Once, s.Twice, s.Never, s.ExtraDollars, s.GaveUp, s.Attempts)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "double-charge", Title: "The agent that charged twice", Run: Run, Report: Report})
}
