// Package cacherouter: routing chat requests across GPU servers that each keep
// a cache of recently seen prompt prefixes.
//
// Most requests to an LLM service start with a long shared prefix — a system
// prompt, a few-shot block, a document. A server that has already processed
// that prefix keeps its attention keys and values (the KV cache) and can skip
// it, so only the new part of the request has to be computed before the first
// token comes out. Whether the next request lands on a server that has its
// prefix decides how much work is done twice.
//
// The model, kept small on purpose:
//   - Each server reads prompts ("prefill") one at a time, at PrefillRate
//     tokens/s. Time to first token = time waiting for that server + prefill.
//     Writing the reply (decode) runs alongside and doesn't block the queue.
//   - Each server caches whole prefixes, least recently used out first, up to
//     CacheTokens.
//   - Prefix popularity follows a Zipf law: a few apps send most traffic.
//
// Policies: round robin; least loaded; cache affinity (consistent hashing of
// the prefix onto a ring of servers); and affinity with a load cap
// (consistent hashing with bounded loads, Mirrokni, Thorup & Zadimoghaddam
// 2018): walk the ring from the prefix's spot to the first server that isn't
// overloaded, so a hot prefix spills over and gets cached on a second server.
package cacherouter

import (
	"encoding/json"
	"fmt"
	"hash/fnv"
	"math"
	"math/rand/v2"
	"sort"
	"strings"

	"miniatures/sims/registry"
)

// Params are what the page's controls change.
type Params struct {
	Policy      string  `json:"policy"`      // round-robin | least-loaded | affinity | bounded
	Servers     int     `json:"servers"`     // GPU servers
	Prefixes    int     `json:"prefixes"`    // distinct shared prefixes (apps)
	Zipf        float64 `json:"zipf"`        // skew of prefix popularity
	Rate        float64 `json:"rate"`        // requests per second
	Duration    float64 `json:"duration"`    // seconds simulated
	CacheTokens int     `json:"cacheTokens"` // per-server prefix cache
	PrefillRate float64 `json:"prefillRate"` // tokens/s a server can prefill
	Bound       float64 `json:"bound"`       // load cap for "bounded", as a multiple of the average
	Seed        uint64  `json:"seed"`
}

// Defaults: a load round robin can only just carry (it recomputes most
// prefixes), so the policies separate clearly.
func Defaults() Params {
	return Params{
		Policy: "bounded", Servers: 8, Prefixes: 24, Zipf: 1.1, Rate: 40, Duration: 60,
		CacheTokens: 12000, PrefillRate: 10000, Bound: 1.25, Seed: 7,
	}
}

// Policies in the order the page shows them.
var Policies = []struct{ Name, Label string }{
	{"round-robin", "Round robin"},
	{"least-loaded", "Least loaded"},
	{"affinity", "Cache affinity"},
	{"bounded", "Affinity with a load cap"},
}

// Prefix is one shared prompt prefix.
type Prefix struct {
	ID     int     `json:"id"`
	Tokens int     `json:"tokens"`
	Share  float64 `json:"share"` // fraction of requests that use it
}

// Req is one request as it went through the system.
type Req struct {
	T       float64 `json:"t"`     // arrival
	Prefix  int     `json:"p"`     // prefix id
	Server  int     `json:"s"`     // server it was sent to
	Hit     bool    `json:"hit"`   // prefix was cached there
	Tokens  int     `json:"tok"`   // tokens prefilled (suffix only on a hit)
	Start   float64 `json:"start"` // prefill starts
	First   float64 `json:"first"` // first token out
	End     float64 `json:"end"`   // last token out
	Evicted []int   `json:"ev,omitempty"`
}

// Stats summarise one policy's run.
type Stats struct {
	Policy      string    `json:"policy"`
	Label       string    `json:"label"`
	HitRate     float64   `json:"hitRate"`     // requests whose prefix was cached
	TokensSaved float64   `json:"tokensSaved"` // fraction of prompt tokens not recomputed
	TTFTMean    float64   `json:"ttftMean"`
	TTFTP50     float64   `json:"ttftP50"`
	TTFTP99     float64   `json:"ttftP99"`
	Busy        []float64 `json:"busy"`    // fraction of time each server spent prefilling
	MaxBusy     float64   `json:"maxBusy"` // the busiest server
}

// Result is what the page gets.
type Result struct {
	Params   Params   `json:"params"`
	Prefixes []Prefix `json:"prefixes"`
	Trace    []Req    `json:"trace"` // the chosen policy's run
	Stats    []Stats  `json:"stats"` // every policy on the same workload
}

type arrival struct {
	t              float64
	prefix, suffix int
	out            int
}

// workload draws the requests; it depends only on the seed, so every policy
// sees exactly the same traffic.
func workload(p Params) ([]Prefix, []arrival) {
	r := rand.New(rand.NewPCG(p.Seed, 1))
	prefixes := make([]Prefix, p.Prefixes)
	var norm float64
	for i := range prefixes {
		w := 1 / math.Pow(float64(i+1), p.Zipf)
		norm += w
		prefixes[i] = Prefix{ID: i, Tokens: 1500 + r.IntN(2500), Share: w}
	}
	cum := make([]float64, len(prefixes))
	acc := 0.0
	for i := range prefixes {
		prefixes[i].Share /= norm
		acc += prefixes[i].Share
		cum[i] = acc
	}
	var reqs []arrival
	for t := r.ExpFloat64() / p.Rate; t < p.Duration; t += r.ExpFloat64() / p.Rate {
		u := r.Float64()
		k := sort.SearchFloat64s(cum, u)
		if k >= len(cum) {
			k = len(cum) - 1
		}
		reqs = append(reqs, arrival{t: t, prefix: k, suffix: 100 + r.IntN(300), out: 50 + r.IntN(250)})
	}
	return prefixes, reqs
}

// lru is one server's prefix cache.
type lru struct {
	cap, used int
	order     []int // least recent first
	size      map[int]int
}

func (c *lru) has(id int) bool { _, ok := c.size[id]; return ok }

func (c *lru) touch(id int) {
	for i, v := range c.order {
		if v == id {
			c.order = append(c.order[:i], c.order[i+1:]...)
			break
		}
	}
	c.order = append(c.order, id)
}

// insert adds a prefix, evicting least recently used ones to make room, and
// returns what it evicted.
func (c *lru) insert(id, tokens int) (evicted []int) {
	if tokens > c.cap {
		return nil
	}
	for c.used+tokens > c.cap {
		old := c.order[0]
		c.order = c.order[1:]
		c.used -= c.size[old]
		delete(c.size, old)
		evicted = append(evicted, old)
	}
	c.size[id] = tokens
	c.used += tokens
	c.order = append(c.order, id)
	return evicted
}

// ring is a consistent-hash ring with virtual nodes.
type ring struct {
	points []uint64
	owner  map[uint64]int
}

func hash64(s string) uint64 {
	h := fnv.New64a()
	h.Write([]byte(s))
	// FNV alone clusters on short similar keys; finish with a mixer.
	x := h.Sum64()
	x ^= x >> 33
	x *= 0xff51afd7ed558ccd
	x ^= x >> 33
	x *= 0xc4ceb9fe1a85ec53
	x ^= x >> 33
	return x
}

func newRing(servers int) ring {
	r := ring{owner: map[uint64]int{}}
	for s := 0; s < servers; s++ {
		for v := 0; v < 64; v++ {
			h := hash64(fmt.Sprintf("server-%d-%d", s, v))
			r.points = append(r.points, h)
			r.owner[h] = s
		}
	}
	sort.Slice(r.points, func(i, j int) bool { return r.points[i] < r.points[j] })
	return r
}

// walk returns the servers in ring order starting from the key's position,
// each once.
func (r ring) walk(key string, servers int) []int {
	h := hash64(key)
	i := sort.Search(len(r.points), func(i int) bool { return r.points[i] >= h })
	seen := make([]bool, servers)
	var out []int
	for k := 0; k < len(r.points) && len(out) < servers; k++ {
		s := r.owner[r.points[(i+k)%len(r.points)]]
		if !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	return out
}

// Simulate runs one policy over the workload.
func Simulate(p Params) (Result, error) {
	if p.Servers < 1 || p.Servers > 64 || p.Prefixes < 1 || p.Prefixes > 500 || p.Rate <= 0 || p.Rate > 500 || p.Duration <= 0 || p.Duration > 600 {
		return Result{}, fmt.Errorf("parameters out of range")
	}
	prefixes, arrivals := workload(p)
	caches := make([]*lru, p.Servers)
	for i := range caches {
		caches[i] = &lru{cap: p.CacheTokens, size: map[int]int{}}
	}
	free := make([]float64, p.Servers) // when each server's prefill queue empties
	busy := make([]float64, p.Servers)
	rg := newRing(p.Servers)
	rr := 0
	trace := make([]Req, 0, len(arrivals))

	backlog := func(s int, now float64) float64 { return math.Max(0, free[s]-now) }
	tie := 0 // rotate where the search starts, so ties don't all go to server 0
	leastLoaded := func(now float64) int {
		tie++
		best := tie % p.Servers
		for k := 1; k < p.Servers; k++ {
			s := (tie + k) % p.Servers
			if backlog(s, now) < backlog(best, now) {
				best = s
			}
		}
		return best
	}

	for _, a := range arrivals {
		var s int
		switch p.Policy {
		case "round-robin":
			s = rr % p.Servers
			rr++
		case "least-loaded":
			s = leastLoaded(a.t)
		case "affinity":
			s = rg.walk(fmt.Sprint("prefix-", a.prefix), p.Servers)[0]
		case "bounded":
			// the cap: Bound times the average backlog, plus one typical
			// prefill so an idle cluster doesn't count as overloaded
			var total float64
			for k := 0; k < p.Servers; k++ {
				total += backlog(k, a.t)
			}
			limit := p.Bound*total/float64(p.Servers) + 0.3
			order := rg.walk(fmt.Sprint("prefix-", a.prefix), p.Servers)
			s = -1
			// prefer a server on the walk that already holds the prefix and
			// is under the cap; otherwise the first one under the cap
			for _, k := range order {
				if caches[k].has(a.prefix) && backlog(k, a.t) <= limit {
					s = k
					break
				}
			}
			if s < 0 {
				for _, k := range order {
					if backlog(k, a.t) <= limit {
						s = k
						break
					}
				}
			}
			if s < 0 {
				s = leastLoaded(a.t)
			}
		default:
			return Result{}, fmt.Errorf("unknown policy %q", p.Policy)
		}

		c := caches[s]
		req := Req{T: a.t, Prefix: a.prefix, Server: s}
		if c.has(a.prefix) {
			req.Hit = true
			req.Tokens = a.suffix
			c.touch(a.prefix)
		} else {
			req.Tokens = prefixes[a.prefix].Tokens + a.suffix
			req.Evicted = c.insert(a.prefix, prefixes[a.prefix].Tokens)
		}
		prefill := float64(req.Tokens) / p.PrefillRate
		req.Start = math.Max(a.t, free[s])
		req.First = req.Start + prefill
		req.End = req.First + float64(a.out)*0.02 // 50 tokens/s while writing
		free[s] = req.First
		busy[s] += prefill
		trace = append(trace, req)
	}

	return Result{Params: p, Prefixes: prefixes, Trace: trace, Stats: []Stats{stats(p, prefixes, trace, busy)}}, nil
}

func stats(p Params, prefixes []Prefix, trace []Req, busy []float64) Stats {
	st := Stats{Policy: p.Policy}
	for _, pol := range Policies {
		if pol.Name == p.Policy {
			st.Label = pol.Label
		}
	}
	ttft := make([]float64, len(trace))
	var hits, saved, total float64
	for i, r := range trace {
		ttft[i] = r.First - r.T
		st.TTFTMean += ttft[i]
		full := float64(prefixes[r.Prefix].Tokens) + float64(r.Tokens)
		if r.Hit {
			hits++
			saved += float64(prefixes[r.Prefix].Tokens)
		} else {
			full = float64(r.Tokens)
		}
		total += full
	}
	if n := float64(len(trace)); n > 0 {
		st.HitRate = hits / n
		st.TTFTMean /= n
	}
	if total > 0 {
		st.TokensSaved = saved / total
	}
	sort.Float64s(ttft)
	st.TTFTP50 = quantile(ttft, 0.5)
	st.TTFTP99 = quantile(ttft, 0.99)
	end := p.Duration
	for _, r := range trace {
		end = math.Max(end, r.First)
	}
	for _, b := range busy {
		st.Busy = append(st.Busy, b/end)
		st.MaxBusy = math.Max(st.MaxBusy, b/end)
	}
	return st
}

func quantile(sorted []float64, q float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	return sorted[int(q*float64(len(sorted)-1))]
}

// Run is the page's entry: the chosen policy's trace, plus every policy's
// numbers on the same workload for the comparison table.
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
	fmt.Fprintf(&b, "%d servers, %d prefixes, %.0f req/s for %.0fs\n\n", res.Params.Servers, res.Params.Prefixes, res.Params.Rate, res.Params.Duration)
	fmt.Fprintf(&b, "%-26s %8s %10s %10s %10s %9s\n", "policy", "hits", "TTFT p50", "TTFT p99", "TTFT mean", "busiest")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-26s %7.0f%% %9.0fms %9.0fms %9.0fms %8.0f%%\n", s.Label, s.HitRate*100, s.TTFTP50*1000, s.TTFTP99*1000, s.TTFTMean*1000, s.MaxBusy*100)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "cache-router", Title: "Routing for a shared prompt cache", Run: Run, Report: Report})
}
