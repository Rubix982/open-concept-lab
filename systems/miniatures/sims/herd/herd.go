// Package herd: a fleet of AI agents sharing one API key with a
// tokens-per-minute limit, and what their retry policy does to it.
//
// The API enforces the limit as a token bucket: it refills continuously at
// TPM/60 tokens a second and holds at most BurstSeconds of refill. A request
// that needs more tokens than the bucket holds is rejected with a 429
// ("too many requests"); the agent learns that one round trip later and
// retries according to its policy. A ten-second outage in the middle of the
// run rejects everything, so every agent ends up retrying at about the same
// moment — the thundering herd.
//
// Policies:
//   - immediate: retry as soon as the 429 arrives
//   - fixed: wait one second, then retry
//   - exponential: wait 0.5 s, 1 s, 2 s, … (capped at 32 s), no randomness
//   - jitter: exponential with "full jitter" — wait a uniform random time
//     between zero and the exponential delay (AWS Architecture Blog,
//     "Exponential Backoff and Jitter", 2015)
//   - shared: the agents draw from one client-side token bucket set a little
//     under the API's limit, and wait their turn locally (first come, first
//     served) instead of being rejected. A rejection opens a circuit breaker:
//     the fleet stops sending, one probe goes out each second, and the first
//     probe that gets through closes the breaker and lets the line move again.
package herd

import (
	"container/heap"
	"encoding/json"
	"fmt"
	"math"
	"math/rand/v2"
	"sort"
	"strings"

	"miniatures/sims/registry"
)

// Params are what the page's controls change.
type Params struct {
	Policy       string  `json:"policy"`       // immediate | fixed | exponential | jitter | shared
	Agents       int     `json:"agents"`       // agents sharing the key
	TPM          float64 `json:"tpm"`          // tokens per minute the API allows
	BurstSeconds float64 `json:"burstSeconds"` // bucket size, in seconds of refill
	Duration     float64 `json:"duration"`     // seconds simulated
	OutageAt     float64 `json:"outageAt"`     // when the API goes down
	OutageLen    float64 `json:"outageLen"`    // for how long (0 = no outage)
	RTT          float64 `json:"rtt"`          // seconds for a rejection to come back
	Seed         uint64  `json:"seed"`
}

// Defaults: the fleet normally wants about 85% of what the key allows, so
// trouble comes from bunching — everyone starting at once, everyone coming
// back after the outage — not from too much work overall.
func Defaults() Params {
	return Params{
		Policy: "jitter", Agents: 100, TPM: 3_500_000, BurstSeconds: 1, Duration: 120,
		OutageAt: 50, OutageLen: 15, RTT: 0.15, Seed: 11,
	}
}

// Policies in the order the page shows them.
var Policies = []struct{ Name, Label string }{
	{"immediate", "Retry immediately"},
	{"fixed", "Wait 1 s"},
	{"exponential", "Exponential backoff"},
	{"jitter", "Exponential + jitter"},
	{"shared", "Shared budget + breaker"},
}

// Agent states, as the page colours them.
const (
	Thinking = iota // working on its own, no request out
	InFlight        // accepted, the reply is being written
	Backoff         // rejected, waiting to retry
	Queued          // waiting its turn at the shared budget
)

const binWidth = 0.25 // seconds per bin of the time series

// Bin is one quarter-second of traffic at the API.
type Bin struct {
	Attempts int `json:"a"` // requests that reached the API
	Limited  int `json:"r"` // rejected with 429
	Outage   int `json:"o"` // rejected because the API was down
	Tokens   int `json:"k"` // tokens accepted
}

// Stats summarise one policy's run.
type Stats struct {
	Policy        string  `json:"policy"`
	Label         string  `json:"label"`
	Completed     int     `json:"completed"`     // requests accepted
	Attempts      int     `json:"attempts"`      // requests sent, accepted or not
	Rejected      int     `json:"rejected"`      // 429s (not counting the outage)
	WastedPerDone float64 `json:"wastedPerDone"` // rejected calls (any reason) per accepted one
	Served        float64 `json:"served"`        // tokens accepted per minute
	Utilisation   float64 `json:"utilisation"`   // of what the limit allowed, outage excluded
	WaitP50       float64 `json:"waitP50"`       // from wanting to send to being accepted
	WaitP95       float64 `json:"waitP95"`
	BigWaitP95    float64 `json:"bigWaitP95"` // the same, for requests over 3,000 tokens
	Fairness      float64 `json:"fairness"`   // Jain's index of requests completed per agent
	MinDone       int     `json:"minDone"`    // the unluckiest agent's completed requests
	MaxDone       int     `json:"maxDone"`
	CatchUp       float64 `json:"catchUp"`     // seconds after the outage until every request it held up got through
	OutageCalls   int     `json:"outageCalls"` // calls sent while the API was down
}

// Result is what the page gets.
type Result struct {
	Params  Params   `json:"params"`
	Rate    float64  `json:"rate"` // the limit in tokens per second
	BinW    float64  `json:"binW"`
	Bins    []Bin    `json:"bins"`
	Events  [][4]int `json:"events"` // [centiseconds, agent, state, tokens/100]
	Done    []int    `json:"done"`   // requests completed per agent
	Stats   []Stats  `json:"stats"`
	Initial []int    `json:"initial"` // each agent's state at t=0
}

// ---- event queue
type event struct {
	t     float64
	seq   int
	agent int
	kind  int
}

const (
	evWant   = iota // the agent wants to send its request
	evReject        // a rejection reaches the agent
	evDone          // the reply finished
	evWake          // the shared budget may have room for the head of the queue
	evProbe         // the breaker is open: try the head of the line once
	evOutageEnd     // the API is back: note who is still waiting
)

type queue []event

func (q queue) Len() int { return len(q) }
func (q queue) Less(i, j int) bool {
	if q[i].t != q[j].t {
		return q[i].t < q[j].t
	}
	return q[i].seq < q[j].seq
}
func (q queue) Swap(i, j int) { q[i], q[j] = q[j], q[i] }
func (q *queue) Push(x any)   { *q = append(*q, x.(event)) }
func (q *queue) Pop() any {
	old := *q
	e := old[len(old)-1]
	*q = old[:len(old)-1]
	return e
}

// bucket is a token bucket that refills lazily.
type bucket struct {
	tokens, cap, rate, last float64
}

func (b *bucket) at(t float64) float64 {
	b.tokens = math.Min(b.cap, b.tokens+b.rate*(t-b.last))
	b.last = t
	return b.tokens
}

type agent struct {
	tokens    int     // size of the current request
	heldUp    bool    // its current request was waiting when the outage ended
	start     float64 // when it first wanted to send it
	failures  int     // consecutive rejections of the current request
	state     int
	completed int
}

// Simulate runs one policy.
func Simulate(p Params) (Result, error) {
	if p.Agents < 1 || p.Agents > 1000 || p.TPM < 10_000 || p.TPM > 1e8 || p.Duration <= 0 || p.Duration > 600 ||
		p.BurstSeconds < 0.1 || p.BurstSeconds > 60 || p.RTT <= 0 || p.RTT > 5 || p.OutageLen < 0 || p.OutageLen > p.Duration {
		return Result{}, fmt.Errorf("parameters out of range")
	}
	known := false
	for _, pol := range Policies {
		known = known || pol.Name == p.Policy
	}
	if !known {
		return Result{}, fmt.Errorf("unknown policy %q", p.Policy)
	}

	r := rand.New(rand.NewPCG(p.Seed, 2))
	// Workload randomness comes from its own stream, per agent, so every
	// policy sees the same request sizes and think times in the same order.
	work := make([]*rand.Rand, p.Agents)
	for i := range work {
		work[i] = rand.New(rand.NewPCG(p.Seed, uint64(1000+i)))
	}
	rate := p.TPM / 60
	server := &bucket{tokens: rate * p.BurstSeconds, cap: rate * p.BurstSeconds, rate: rate}
	client := &bucket{tokens: 0.97 * rate * p.BurstSeconds, cap: 0.97 * rate * p.BurstSeconds, rate: 0.97 * rate}

	nb := int(math.Ceil(p.Duration / binWidth))
	res := Result{Params: p, Rate: rate, BinW: binWidth, Bins: make([]Bin, nb), Done: make([]int, p.Agents)}
	agents := make([]agent, p.Agents)
	var waits, bigWaits []float64
	var stats Stats
	catchUp := 0.0

	q := &queue{}
	seq := 0
	push := func(t float64, a, kind int) {
		seq++
		heap.Push(q, event{t: t, seq: seq, agent: a, kind: kind})
	}
	setState := func(t float64, a, s int) {
		if agents[a].state == s {
			return
		}
		agents[a].state = s
		res.Events = append(res.Events, [4]int{int(math.Round(t * 100)), a, s, agents[a].tokens / 100})
	}
	bin := func(t float64) *Bin {
		k := int(t / binWidth)
		if k >= nb {
			k = nb - 1
		}
		return &res.Bins[k]
	}
	newTask := func(a int) {
		agents[a].tokens = 500 + work[a].IntN(3501)
		agents[a].failures = 0
	}
	think := func(a int) float64 { return 1 + 3*work[a].Float64() }

	// everyone starts within the first half second: the fleet comes up together
	for a := 0; a < p.Agents; a++ {
		newTask(a)
		t := 0.5 * work[a].Float64()
		agents[a].start = t
		push(t, a, evWant)
		res.Initial = append(res.Initial, Thinking)
	}

	if p.OutageLen > 0 {
		push(p.OutageAt+p.OutageLen, -1, evOutageEnd)
	}

	backoff := func(a int) float64 {
		k := agents[a].failures
		exp := math.Min(32, 0.5*math.Pow(2, float64(k-1)))
		switch p.Policy {
		case "immediate":
			return 0
		case "fixed":
			return 1
		case "exponential":
			return exp
		default: // jitter, and outage errors under the shared budget
			return r.Float64() * exp
		}
	}

	// send puts the request in front of the API.
	send := func(t float64, a int) bool {
		b := bin(t)
		b.Attempts++
		stats.Attempts++
		down := p.OutageLen > 0 && t >= p.OutageAt && t < p.OutageAt+p.OutageLen
		tok := float64(agents[a].tokens)
		if !down && server.at(t) >= tok {
			server.tokens -= tok
			b.Tokens += agents[a].tokens
			stats.Completed++
			agents[a].completed++
			if agents[a].heldUp {
				agents[a].heldUp = false
				catchUp = math.Max(catchUp, t-(p.OutageAt+p.OutageLen))
			}
			w := t - agents[a].start
			waits = append(waits, w)
			if agents[a].tokens > 3000 {
				bigWaits = append(bigWaits, w)
			}
			setState(t, a, InFlight)
			push(t+1+tok/2000, a, evDone) // writing the reply
			return true
		}
		if down {
			b.Outage++
			stats.OutageCalls++
		} else {
			b.Limited++
			stats.Rejected++
		}
		agents[a].failures++
		setState(t, a, Backoff)
		push(t+p.RTT, a, evReject)
		return false
	}

	// the shared budget: first come, first served
	var line []int
	wakePending, breakerOpen, probePending := false, false, false
	serve := func(t float64) {
		if breakerOpen {
			return
		}
		for len(line) > 0 && client.at(t) >= float64(agents[line[0]].tokens) {
			a := line[0]
			line = line[1:]
			client.tokens -= float64(agents[a].tokens)
			send(t, a)
		}
		if len(line) > 0 && !wakePending {
			need := float64(agents[line[0]].tokens) - client.at(t)
			wakePending = true
			push(t+need/client.rate+1e-9, -1, evWake)
		}
	}

	for q.Len() > 0 {
		e := heap.Pop(q).(event)
		if e.t >= p.Duration {
			break
		}
		switch e.kind {
		case evWant:
			if p.Policy == "shared" {
				setState(e.t, e.agent, Queued)
				line = append(line, e.agent)
				serve(e.t)
			} else {
				send(e.t, e.agent)
			}
		case evReject:
			if p.Policy == "shared" {
				// back to the front of the line; stop the fleet and probe
				setState(e.t, e.agent, Queued)
				line = append([]int{e.agent}, line...)
				breakerOpen = true
				if !probePending {
					probePending = true
					push(e.t+1, -1, evProbe)
				}
				break
			}
			push(e.t+backoff(e.agent), e.agent, evWant)
		case evProbe:
			probePending = false
			if len(line) == 0 {
				breakerOpen = false
				break
			}
			a := line[0]
			line = line[1:]
			client.at(e.t)
			client.tokens -= float64(agents[a].tokens) // the probe spends from the budget too
			if send(e.t, a) {
				breakerOpen = false
				serve(e.t)
			}
		case evDone:
			setState(e.t, e.agent, Thinking)
			newTask(e.agent)
			next := e.t + think(e.agent)
			agents[e.agent].start = next
			push(next, e.agent, evWant)
		case evWake:
			wakePending = false
			serve(e.t)
		case evOutageEnd:
			for a := range agents {
				if agents[a].state == Backoff || agents[a].state == Queued {
					agents[a].heldUp = true
				}
			}
		}
	}

	// requests still waiting at the end count as waiting until the end
	for a := range agents {
		res.Done[a] = agents[a].completed
		if agents[a].state != InFlight && agents[a].state != Thinking && agents[a].start < p.Duration {
			w := p.Duration - agents[a].start
			waits = append(waits, w)
			if agents[a].tokens > 3000 {
				bigWaits = append(bigWaits, w)
			}
		}
	}

	stats.Policy = p.Policy
	for _, pol := range Policies {
		if pol.Name == p.Policy {
			stats.Label = pol.Label
		}
	}
	var served float64
	var rejectedAll int
	for _, b := range res.Bins {
		served += float64(b.Tokens)
		rejectedAll += b.Limited + b.Outage
	}
	stats.Served = served / p.Duration * 60
	allowed := rate*(p.Duration-p.OutageLen) + 2*server.cap // plus a full bucket at the start and after the outage
	stats.Utilisation = served / allowed
	if stats.Completed > 0 {
		stats.WastedPerDone = float64(rejectedAll) / float64(stats.Completed)
	}
	sort.Float64s(waits)
	sort.Float64s(bigWaits)
	stats.WaitP50 = quantile(waits, 0.5)
	stats.WaitP95 = quantile(waits, 0.95)
	stats.BigWaitP95 = quantile(bigWaits, 0.95)
	var s1, s2 float64
	stats.MinDone = math.MaxInt
	for _, d := range res.Done {
		s1 += float64(d)
		s2 += float64(d) * float64(d)
		stats.MinDone = min(stats.MinDone, d)
		stats.MaxDone = max(stats.MaxDone, d)
	}
	if s2 > 0 {
		stats.Fairness = s1 * s1 / (float64(len(res.Done)) * s2)
	}
	for a := range agents {
		if agents[a].heldUp { // never got through before the run ended
			catchUp = p.Duration - (p.OutageAt + p.OutageLen)
		}
	}
	stats.CatchUp = catchUp
	res.Stats = []Stats{stats}
	return res, nil
}

func quantile(sorted []float64, q float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	return sorted[int(q*float64(len(sorted)-1))]
}

// Run is the page's entry: the chosen policy's trace, plus every policy's
// numbers on the same workload.
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
	fmt.Fprintf(&b, "%d agents, %.0fk tokens/min limit, %.0fs, outage at %.0fs for %.0fs\n\n", p.Agents, p.TPM/1000, p.Duration, p.OutageAt, p.OutageLen)
	fmt.Fprintf(&b, "%-24s %6s %6s %15s %7s %9s %9s %9s %6s\n", "policy", "done", "429s", "calls in outage", "waste", "wait p50", "wait p95", "catch-up", "fair")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-24s %6d %6d %15d %6.1fx %8.1fs %8.1fs %8.1fs %6.2f\n",
			s.Label, s.Completed, s.Rejected, s.OutageCalls, s.WastedPerDone, s.WaitP50, s.WaitP95, s.CatchUp, s.Fairness)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "herd", Title: "A hundred agents, one rate limit", Run: Run, Report: Report})
}
