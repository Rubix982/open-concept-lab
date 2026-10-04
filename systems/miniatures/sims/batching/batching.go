// Package batching: one GPU writing replies for many requests at once, and
// two ways to decide who gets a seat in the batch.
//
// A GPU writes a reply one token at a time, but it can advance several
// replies in the same step for little extra cost: a step with b replies takes
// StepBase + StepPer·b. So it runs a batch of up to Slots replies together.
//
// Replies vary wildly in length — most are short, a few run long.
//
//   - Static batching takes up to Slots waiting requests and runs them until
//     every one has finished. A reply that ends early leaves its seat empty
//     until the longest reply in the batch is done, and anyone who arrives in
//     the meantime waits for the whole batch.
//   - Continuous batching (iteration-level scheduling, Yu et al., "Orca",
//     OSDI 2022) looks at the queue before every step and fills any empty seat
//     straight away.
//
// A request joining the batch also has its prompt read in the step it joins,
// which adds PromptTokens/PrefillRate to that step.
package batching

import (
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
	Policy      string  `json:"policy"`      // static | continuous
	Slots       int     `json:"slots"`       // seats in the batch
	Rate        float64 `json:"rate"`        // requests per second
	Spread      float64 `json:"spread"`      // how heavy the long tail of reply lengths is
	Median      int     `json:"median"`      // median reply length, tokens
	Duration    float64 `json:"duration"`    // seconds of arrivals
	StepBase    float64 `json:"stepBase"`    // seconds per step, fixed part
	StepPer     float64 `json:"stepPer"`     // seconds per step, per reply in it
	PrefillRate float64 `json:"prefillRate"` // prompt tokens read per second
	Seed        uint64  `json:"seed"`
}

// Defaults: a load continuous batching carries comfortably and static
// batching can't.
func Defaults() Params {
	return Params{
		Policy: "continuous", Slots: 8, Rate: 1.5, Spread: 1.0, Median: 80, Duration: 60,
		StepBase: 0.020, StepPer: 0.002, PrefillRate: 20000, Seed: 3,
	}
}

// Policies in the order the page shows them.
var Policies = []struct{ Name, Label string }{
	{"static", "Static batching"},
	{"continuous", "Continuous batching"},
}

// Req is one request as it went through the GPU.
type Req struct {
	T      float64 `json:"t"`     // arrival
	Out    int     `json:"out"`   // reply length, tokens
	Prompt int     `json:"in"`    // prompt length, tokens
	Slot   int     `json:"slot"`  // seat it got
	Start  float64 `json:"start"` // its first step begins
	First  float64 `json:"first"` // first token out
	End    float64 `json:"end"`   // last token out
}

// Step is one GPU step: when it ran, how many seats were in use, and how many
// requests were already waiting but not let in.
type Step struct {
	S     float64 `json:"s"`
	E     float64 `json:"e"`
	N     int     `json:"n"`
	Queue int     `json:"q"`
}

// Stats summarise one policy's run.
type Stats struct {
	Policy      string  `json:"policy"`
	Label       string  `json:"label"`
	Throughput  float64 `json:"throughput"`  // reply tokens per second, over the whole run
	LatencyMean float64 `json:"latencyMean"` // arrival to last token
	LatencyP99  float64 `json:"latencyP99"`
	TTFTMean    float64 `json:"ttftMean"`    // arrival to first token
	Utilisation float64 `json:"utilisation"` // seat-steps doing work
	Wasted      float64 `json:"wasted"`      // seat-steps empty while someone waited
	Makespan    float64 `json:"makespan"`    // when the last reply finished
}

// Result is what the page gets.
type Result struct {
	Params Params  `json:"params"`
	Trace  []Req   `json:"trace"`
	Steps  []Step  `json:"steps"`
	Stats  []Stats `json:"stats"`
}

type arrival struct {
	t           float64
	out, prompt int
}

// workload depends only on the seed, so both policies see the same traffic.
func workload(p Params) []arrival {
	r := rand.New(rand.NewPCG(p.Seed, 2))
	var out []arrival
	for t := r.ExpFloat64() / p.Rate; t < p.Duration; t += r.ExpFloat64() / p.Rate {
		// log-normal reply lengths around the median, clipped to 10..1200
		n := float64(p.Median) * math.Exp(p.Spread*r.NormFloat64())
		n = math.Max(10, math.Min(1200, math.Round(n)))
		out = append(out, arrival{t: t, out: int(n), prompt: 200 + r.IntN(400)})
	}
	return out
}

// Simulate runs one policy.
func Simulate(p Params) (Result, error) {
	if p.Slots < 1 || p.Slots > 64 || p.Rate <= 0 || p.Rate > 20 || p.Spread < 0 || p.Spread > 2.5 ||
		p.Median < 5 || p.Median > 1000 || p.Duration <= 0 || p.Duration > 300 || p.StepBase <= 0 || p.StepPer < 0 || p.PrefillRate <= 0 {
		return Result{}, fmt.Errorf("parameters out of range")
	}
	if p.Policy != "static" && p.Policy != "continuous" {
		return Result{}, fmt.Errorf("unknown policy %q", p.Policy)
	}
	arr := workload(p)
	reqs := make([]Req, len(arr))
	for i, a := range arr {
		reqs[i] = Req{T: a.t, Out: a.out, Prompt: a.prompt, Slot: -1}
	}
	seats := make([]int, p.Slots) // request index per seat, -1 empty
	left := make([]int, p.Slots)  // tokens still to write
	for i := range seats {
		seats[i] = -1
	}
	next, done := 0, 0 // next arrival not yet queued; finished requests
	var queue []int
	var steps []Step
	now := 0.0
	active := 0
	const maxSteps = 400000 // guard against runaway runs in the browser
	for done < len(reqs) {
		for next < len(reqs) && reqs[next].T <= now {
			queue = append(queue, next)
			next++
		}
		// admit: continuous fills empty seats every step; static only when
		// the whole batch has finished
		joined := 0.0
		if p.Policy == "continuous" || active == 0 {
			for s := 0; s < p.Slots && len(queue) > 0; s++ {
				if seats[s] >= 0 {
					continue
				}
				i := queue[0]
				queue = queue[1:]
				seats[s], left[s] = i, reqs[i].Out
				reqs[i].Slot, reqs[i].Start = s, now
				joined += float64(reqs[i].Prompt) / p.PrefillRate
				active++
			}
		}
		if active == 0 {
			now = reqs[next].T // idle: jump to the next arrival
			continue
		}
		dt := p.StepBase + p.StepPer*float64(active) + joined
		// requests already queued when the step starts and not let in; anyone
		// arriving mid-step couldn't have joined it under either policy
		steps = append(steps, Step{S: now, E: now + dt, N: active, Queue: len(queue)})
		now += dt
		for s := range seats {
			i := seats[s]
			if i < 0 {
				continue
			}
			left[s]--
			if left[s] == reqs[i].Out-1 {
				reqs[i].First = now
			}
			if left[s] == 0 {
				reqs[i].End = now
				seats[s] = -1
				active--
				done++
			}
		}
		if len(steps) > maxSteps {
			return Result{}, fmt.Errorf("run too long; lower the load")
		}
	}
	return Result{Params: p, Trace: reqs, Steps: steps, Stats: []Stats{stats(p, reqs, steps)}}, nil
}

func stats(p Params, reqs []Req, steps []Step) Stats {
	st := Stats{Policy: p.Policy}
	for _, pol := range Policies {
		if pol.Name == p.Policy {
			st.Label = pol.Label
		}
	}
	var tokens float64
	lat := make([]float64, len(reqs))
	for i, r := range reqs {
		tokens += float64(r.Out)
		lat[i] = r.End - r.T
		st.LatencyMean += lat[i]
		st.TTFTMean += r.First - r.T
		st.Makespan = math.Max(st.Makespan, r.End)
	}
	if n := float64(len(reqs)); n > 0 {
		st.LatencyMean /= n
		st.TTFTMean /= n
	}
	sort.Float64s(lat)
	if len(lat) > 0 {
		st.LatencyP99 = lat[int(0.99*float64(len(lat)-1))]
	}
	var used, total, wasted float64
	for _, s := range steps {
		d := s.E - s.S
		used += float64(s.N) * d
		total += float64(p.Slots) * d
		empty := p.Slots - s.N
		if s.Queue < empty {
			empty = s.Queue
		}
		wasted += float64(empty) * d
	}
	if total > 0 {
		st.Utilisation = used / total
		st.Wasted = wasted / total
	}
	if st.Makespan > 0 {
		st.Throughput = tokens / st.Makespan
	}
	return st
}

// Run is the page's entry: the chosen policy's trace, plus both policies'
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
	var b strings.Builder
	fmt.Fprintf(&b, "1 GPU, %d seats, %.1f req/s for %.0fs, median reply %d tokens (spread %.1f)\n\n",
		res.Params.Slots, res.Params.Rate, res.Params.Duration, res.Params.Median, res.Params.Spread)
	fmt.Fprintf(&b, "%-22s %10s %11s %11s %10s %9s %8s\n", "policy", "tokens/s", "lat mean", "lat p99", "TTFT", "seats", "wasted")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-22s %10.0f %10.1fs %10.1fs %9.1fs %8.0f%% %7.0f%%\n",
			s.Label, s.Throughput, s.LatencyMean, s.LatencyP99, s.TTFTMean, s.Utilisation*100, s.Wasted*100)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "batching", Title: "Continuous batching", Run: Run, Report: Report})
}
