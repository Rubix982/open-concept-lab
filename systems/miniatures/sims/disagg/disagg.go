// Package disagg: serving LLM requests when reading the prompt and writing
// the reply compete for the same GPU.
//
// A request has two phases. Prefill reads the whole prompt in one big
// compute-bound pass and produces the first token. Decode then writes the
// reply one token at a time; every step is small, and a GPU batches all the
// replies it is writing into one step ("iteration"). The two phases want
// different things: prefill is a large burst, decode needs a steady, quick
// rhythm. Put them on the same GPU and every long prompt that arrives freezes
// all the replies being written there.
//
// The model, kept small on purpose. Each GPU runs iterations back to back;
// an iteration writes one token for every reply in progress and may also read
// some prompt tokens:
//
//	iteration time = Base + PerSeq × replies + PerPrefillToken × prompt tokens read
//
// Policies:
//   - colocated: every GPU does both; waiting prompts are read whole in the
//     next iteration (up to a token budget), so that iteration is long and
//     every reply on the GPU stalls with it.
//   - chunked: as colocated, but at most Chunk prompt tokens are read per
//     iteration, so a long prompt is spread over many slightly slower
//     iterations (the idea of Sarathi-Serve, OSDI 2024).
//   - disaggregated: PrefillGPUs only read prompts; the rest only write
//     replies. When a prompt is read its KV cache is shipped to a writing GPU,
//     taking KVPerToken seconds per prompt token (DistServe, OSDI 2024;
//     Splitwise, ISCA 2024).
//
// A request is on time when its first token comes within SLOTTFT and its
// reply streams smoothly: the average gap between tokens is within SLOTPOT
// and no single pause is longer than SLOPause. Averages alone hide the
// problem — a reply that freezes for half a second twice still averages fast.
package disagg

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
	Policy          string  `json:"policy"`          // colocated | chunked | disaggregated
	GPUs            int     `json:"gpus"`            // GPUs in the pool
	PrefillGPUs     int     `json:"prefillGPUs"`     // of those, how many only read prompts (disaggregated)
	Rate            float64 `json:"rate"`            // requests per second
	Duration        float64 `json:"duration"`        // seconds of arrivals
	LongShare       float64 `json:"longShare"`       // fraction of requests with a long prompt
	Base            float64 `json:"base"`            // seconds per iteration, fixed
	PerSeq          float64 `json:"perSeq"`          // seconds per reply in the batch
	PerPrefillToken float64 `json:"perPrefillToken"` // seconds per prompt token read
	Budget          int     `json:"budget"`          // max prompt tokens read whole in one iteration
	Chunk           int     `json:"chunk"`           // prompt tokens per iteration when chunked
	KVPerToken      float64 `json:"kvPerToken"`      // seconds per prompt token to ship the KV cache
	SLOTTFT         float64 `json:"sloTTFT"`         // first-token target, seconds
	SLOTPOT         float64 `json:"sloTPOT"`         // average gap between tokens target, seconds
	SLOPause        float64 `json:"sloPause"`        // longest single pause allowed, seconds
	Samples         int     `json:"samples"`         // requests whose every token time is kept for the page
	Seed            uint64  `json:"seed"`
}

// Defaults: four GPUs split two and two, three prompts in ten long, at a
// load where putting both jobs on one GPU visibly stutters.
func Defaults() Params {
	return Params{
		Policy: "disaggregated", GPUs: 4, PrefillGPUs: 2, Rate: 14, Duration: 40, LongShare: 0.3,
		Base: 0.012, PerSeq: 0.0004, PerPrefillToken: 0.00005, Budget: 8192, Chunk: 512,
		KVPerToken: 0.00001, SLOTTFT: 2, SLOTPOT: 0.05, SLOPause: 0.25, Samples: 6, Seed: 11,
	}
}

// Policies in the order the page shows them.
var Policies = []struct{ Name, Label string }{
	{"colocated", "Same GPU, whole prompts"},
	{"chunked", "Same GPU, prompts in chunks"},
	{"disaggregated", "Separate GPUs"},
}

// Iter is one GPU iteration: [gpu, start, duration, prompt tokens read, replies written].
type Iter [5]float64

// Req is one request's outcome.
type Req struct {
	T      float64 `json:"t"`      // arrival
	Prompt int     `json:"prompt"` // prompt tokens
	Out    int     `json:"out"`    // reply tokens
	PGPU   int     `json:"pg"`     // GPU that read the prompt
	DGPU   int     `json:"dg"`     // GPU that wrote the reply
	First  float64 `json:"first"`  // first token (-1 if never)
	End    float64 `json:"end"`    // last token (-1 if never)
	TPOT   float64 `json:"tpot"`   // average gap between tokens
	MaxGap float64 `json:"maxGap"` // longest pause between two tokens
	OK     bool    `json:"ok"`     // met both targets
}

// Sample keeps every token time of one request, for the token-stream view.
type Sample struct {
	ID     int       `json:"id"`
	Tokens []float64 `json:"tokens"`
}

// Stats summarise one policy's run.
type Stats struct {
	Policy   string  `json:"policy"`
	Label    string  `json:"label"`
	TTFTP50  float64 `json:"ttftP50"`
	TTFTP90  float64 `json:"ttftP90"`
	TPOTP50  float64 `json:"tpotP50"`
	TPOTP90  float64 `json:"tpotP90"`
	GapP90   float64 `json:"gapP90"`  // 90th percentile of each request's longest pause
	GapMax   float64 `json:"gapMax"`  // the longest pause anyone saw
	Goodput  float64 `json:"goodput"` // fraction meeting both targets
	Finished float64 `json:"finished"`
}

// Result is what the page gets.
type Result struct {
	Params  Params   `json:"params"`
	Iters   []Iter   `json:"iters"`
	Reqs    []Req    `json:"reqs"`
	Samples []Sample `json:"samples"`
	End     float64  `json:"end"`
	Stats   []Stats  `json:"stats"`
}

type arrival struct {
	t           float64
	prompt, out int
}

// workload depends only on the seed, so every policy sees the same traffic.
func workload(p Params) []arrival {
	r := rand.New(rand.NewPCG(p.Seed, 3))
	var out []arrival
	for t := r.ExpFloat64() / p.Rate; t < p.Duration; t += r.ExpFloat64() / p.Rate {
		prompt := 200 + r.IntN(1000)
		if r.Float64() < p.LongShare {
			prompt = 3000 + r.IntN(5000)
		}
		out = append(out, arrival{t: t, prompt: prompt, out: 100 + r.IntN(300)})
	}
	return out
}

type seq struct {
	id          int
	left        int // prompt tokens still to read
	produced    int
	last        float64
	gapSum      float64
	sample      bool
	tokens      []float64
	reqIdx      int
	sinceInsert bool
}

type gpu struct {
	id      int
	role    string // both | prefill | decode
	waiting []*seq // prompts not yet fully read, first come first served
	active  []*seq // replies being written
	busy    bool
	end     float64
	// what the running iteration is doing
	reading []struct {
		s *seq
		n int
	}
	writing []*seq
}

type ship struct {
	at float64
	s  *seq
	g  int
}

// Simulate runs one policy.
func Simulate(p Params) (Result, error) {
	if p.GPUs < 1 || p.GPUs > 16 || p.Rate <= 0 || p.Rate > 60 || p.Duration <= 0 || p.Duration > 120 ||
		p.LongShare < 0 || p.LongShare > 1 || p.Chunk < 16 || p.Budget < 1024 || p.Base <= 0 {
		return Result{}, fmt.Errorf("parameters out of range")
	}
	if p.Policy == "disaggregated" && (p.PrefillGPUs < 1 || p.PrefillGPUs >= p.GPUs) {
		return Result{}, fmt.Errorf("separate GPUs need at least one GPU of each kind")
	}
	arrivals := workload(p)
	reqs := make([]Req, len(arrivals))
	seqs := make([]*seq, len(arrivals))
	// samples: evenly spaced through the middle half of the run
	sampled := map[int]bool{}
	for k := 0; k < p.Samples && len(arrivals) > 0; k++ {
		i := len(arrivals)/4 + k*len(arrivals)/(2*max(1, p.Samples))
		sampled[min(i, len(arrivals)-1)] = true
	}
	gpus := make([]*gpu, p.GPUs)
	for i := range gpus {
		role := "both"
		if p.Policy == "disaggregated" {
			role = "decode"
			if i < p.PrefillGPUs {
				role = "prefill"
			}
		}
		gpus[i] = &gpu{id: i, role: role}
	}
	var iters []Iter
	var ships []ship
	hardStop := p.Duration*6 + 60

	// start an iteration on g at time now, if it has anything to do
	start := func(g *gpu, now float64) {
		g.reading = g.reading[:0]
		g.writing = g.writing[:0]
		if g.role != "prefill" {
			g.writing = append(g.writing, g.active...)
		}
		tokens := 0
		if g.role != "decode" {
			budget := p.Budget
			if p.Policy == "chunked" {
				budget = p.Chunk
			}
			for _, s := range g.waiting {
				if tokens >= budget {
					break
				}
				n := s.left
				if p.Policy == "chunked" {
					n = min(n, budget-tokens)
				} else if tokens > 0 && tokens+n > budget {
					break // whole prompts only; the first one always fits
				}
				g.reading = append(g.reading, struct {
					s *seq
					n int
				}{s, n})
				tokens += n
			}
		}
		if len(g.writing) == 0 && len(g.reading) == 0 {
			g.busy = false
			return
		}
		dur := p.Base + p.PerSeq*float64(len(g.writing)) + p.PerPrefillToken*float64(tokens)
		g.busy = true
		g.end = now + dur
		iters = append(iters, Iter{float64(g.id), round(now), round(dur), float64(tokens), float64(len(g.writing))})
	}

	emit := func(s *seq, at float64) {
		r := &reqs[s.reqIdx]
		if s.produced == 0 {
			r.First = at
		} else {
			gap := at - s.last
			s.gapSum += gap
			r.MaxGap = math.Max(r.MaxGap, gap)
		}
		s.produced++
		s.last = at
		if s.sample {
			s.tokens = append(s.tokens, round(at))
		}
		if s.produced == r.Out {
			r.End = at
			if r.Out > 1 {
				r.TPOT = s.gapSum / float64(r.Out-1)
			}
		}
	}

	// finish g's iteration at its end time
	finish := func(g *gpu) {
		now := g.end
		var still []*seq
		written := map[*seq]bool{}
		for _, s := range g.writing {
			written[s] = true
			emit(s, now)
		}
		for _, s := range g.active {
			if reqs[s.reqIdx].End < 0 {
				still = append(still, s)
			} else if !written[s] {
				still = append(still, s)
			}
		}
		g.active = still
		for _, rd := range g.reading {
			s := rd.s
			s.left -= rd.n
			if s.left == 0 {
				// the prompt is read: that pass produces the first token
				for i, w := range g.waiting {
					if w == s {
						g.waiting = append(g.waiting[:i], g.waiting[i+1:]...)
						break
					}
				}
				emit(s, now)
				if p.Policy == "disaggregated" {
					// ship the KV cache to the writing GPU with the fewest replies
					best := -1
					for _, h := range gpus {
						if h.role == "decode" && (best < 0 || len(h.active) < len(gpus[best].active)) {
							best = h.id
						}
					}
					reqs[s.reqIdx].DGPU = best
					ships = append(ships, ship{at: now + p.KVPerToken*float64(reqs[s.reqIdx].Prompt), s: s, g: best})
				} else if reqs[s.reqIdx].End < 0 {
					g.active = append(g.active, s)
				}
			}
		}
		start(g, now)
	}

	next := 0
	for {
		// the earliest pending event
		t, kind, which := math.Inf(1), "", -1
		if next < len(arrivals) {
			t, kind = arrivals[next].t, "arrive"
		}
		for _, g := range gpus {
			if g.busy && g.end < t {
				t, kind, which = g.end, "iter", g.id
			}
		}
		for i, sh := range ships {
			if sh.at < t {
				t, kind, which = sh.at, "ship", i
			}
		}
		if kind == "" || t > hardStop {
			break
		}
		switch kind {
		case "arrive":
			a := arrivals[next]
			s := &seq{id: next, left: a.prompt, reqIdx: next, sample: sampled[next]}
			seqs[next] = s
			reqs[next] = Req{T: round(a.t), Prompt: a.prompt, Out: a.out, First: -1, End: -1, PGPU: -1, DGPU: -1}
			// to the GPU that can read prompts with the least outstanding work
			best := -1
			var bestLoad float64
			for _, g := range gpus {
				if g.role == "decode" {
					continue
				}
				load := 0.0
				for _, w := range g.waiting {
					load += float64(w.left) * p.PerPrefillToken
				}
				if g.role == "both" {
					load += float64(len(g.active)) * 0.05
				}
				if best < 0 || load < bestLoad {
					best, bestLoad = g.id, load
				}
			}
			g := gpus[best]
			reqs[next].PGPU = best
			if g.role == "both" {
				reqs[next].DGPU = best
			}
			g.waiting = append(g.waiting, s)
			next++
			if !g.busy {
				start(g, a.t)
			}
		case "iter":
			finish(gpus[which])
		case "ship":
			sh := ships[which]
			ships = append(ships[:which], ships[which+1:]...)
			g := gpus[sh.g]
			g.active = append(g.active, sh.s)
			if !g.busy {
				start(g, sh.at)
			}
		}
	}

	res := Result{Params: p, Iters: iters, Reqs: reqs}
	for _, s := range seqs {
		if s != nil && s.sample {
			res.Samples = append(res.Samples, Sample{ID: s.id, Tokens: s.tokens})
		}
	}
	for i := range reqs {
		r := &reqs[i]
		r.First, r.End, r.TPOT, r.MaxGap = round(r.First), round(r.End), round(r.TPOT), round(r.MaxGap)
		r.OK = r.End >= 0 && r.First-r.T <= p.SLOTTFT && r.TPOT <= p.SLOTPOT && r.MaxGap <= p.SLOPause
		res.End = math.Max(res.End, r.End)
	}
	res.End = math.Max(res.End, p.Duration)
	res.Stats = []Stats{stats(p, reqs)}
	return res, nil
}

func round(x float64) float64 { return math.Round(x*1e4) / 1e4 }

func stats(p Params, reqs []Req) Stats {
	st := Stats{Policy: p.Policy}
	for _, pol := range Policies {
		if pol.Name == p.Policy {
			st.Label = pol.Label
		}
	}
	var ttft, tpot, gap []float64
	ok, done := 0, 0
	for _, r := range reqs {
		if r.End < 0 {
			continue
		}
		done++
		if r.OK {
			ok++
		}
		ttft = append(ttft, r.First-r.T)
		tpot = append(tpot, r.TPOT)
		gap = append(gap, r.MaxGap)
		st.GapMax = math.Max(st.GapMax, r.MaxGap)
	}
	for _, xs := range [][]float64{ttft, tpot, gap} {
		sort.Float64s(xs)
	}
	st.TTFTP50, st.TTFTP90 = q(ttft, 0.5), q(ttft, 0.9)
	st.TPOTP50, st.TPOTP90 = q(tpot, 0.5), q(tpot, 0.9)
	st.GapP90 = q(gap, 0.9)
	if len(reqs) > 0 {
		st.Goodput = float64(ok) / float64(len(reqs))
		st.Finished = float64(done) / float64(len(reqs))
	}
	return st
}

func q(sorted []float64, f float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	return sorted[int(f*float64(len(sorted)-1))]
}

// Run is the page's entry: the chosen policy's run, plus every policy's
// numbers on the same traffic for the comparison table.
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
	fmt.Fprintf(&b, "%d GPUs (%d reading prompts when separate), %.0f req/s for %.0fs, %.0f%% long prompts\n", p.GPUs, p.PrefillGPUs, p.Rate, p.Duration, p.LongShare*100)
	fmt.Fprintf(&b, "on time: first token within %.1fs, average gap within %.0fms, no pause over %.0fms\n\n", p.SLOTTFT, p.SLOTPOT*1000, p.SLOPause*1000)
	fmt.Fprintf(&b, "%-28s %9s %9s %9s %9s %10s %10s %9s\n", "policy", "TTFT p50", "TTFT p90", "TPOT p50", "TPOT p90", "pause p90", "worst", "on time")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-28s %7.0fms %7.0fms %7.0fms %7.0fms %8.0fms %8.0fms %8.0f%%\n", s.Label,
			s.TTFTP50*1000, s.TTFTP90*1000, s.TPOTP50*1000, s.TPOTP90*1000, s.GapP90*1000, s.GapMax*1000, s.Goodput*100)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "disagg", Title: "Splitting prompt reading from writing", Run: Run, Report: Report})
}
