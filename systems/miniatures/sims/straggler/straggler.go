// Package straggler: synchronous training on many GPUs, where every step waits
// for the slowest GPU and every failure throws work back to the last
// checkpoint.
//
// Two effects, both measured:
//
//   - Stragglers. Each step, every GPU computes for Base seconds times a small
//     random jitter, and with a small probability a GPU is SlowFactor times
//     slower that step (thermal throttling, a noisy neighbour). Then all GPUs
//     synchronise (the all-reduce, a fixed Sync seconds here). The step lasts
//     as long as the slowest GPU. The chance that *some* GPU is slow on a given
//     step grows with the number of GPUs, so the average step gets longer.
//     The maximum of N jittered GPUs is sampled directly from the distribution
//     of the maximum, and the number of slow GPUs from a Poisson draw, so a
//     step costs the same to simulate at 8 GPUs as at 16,384.
//     Mitigation: backup workers (Chen et al., "Revisiting Distributed
//     Synchronous SGD", 2016): run 2% extra GPUs and finish the step when the
//     first N have reported, so a few slow ones are simply not waited for.
//
//   - Failures. Each GPU fails independently; the cluster's mean time between
//     failures is the per-GPU figure divided by N. A failure loses all work
//     since the last checkpoint plus a restart; a checkpoint every Interval
//     costs CkptCost. The interval that balances the two is close to the
//     Young/Daly value sqrt(2 * CkptCost * clusterMTBF).
//
// The default failure rate is set from what Meta reported for Llama 3
// pre-training: 419 unexpected interruptions in a 54-day period on 16,384
// GPUs ("The Llama 3 Herd of Models", 2024), about one every 3.1 hours.
package straggler

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand/v2"
	"strings"

	"miniatures/sims/registry"
)

// Params are what the page's controls change. Times: seconds for a step,
// minutes for checkpoints and restarts, hours for MTBF, days for the run.
type Params struct {
	GPUs       int     `json:"gpus"`       // 8 … 16384
	Backup     bool    `json:"backup"`     // run 2% backup GPUs and don't wait for the slowest
	Interval   float64 `json:"interval"`   // minutes of training between checkpoints
	CkptCost   float64 `json:"ckptCost"`   // minutes to write a checkpoint
	Restart    float64 `json:"restart"`    // minutes to recover after a failure
	SlowProb   float64 `json:"slowProb"`   // chance a given GPU is slow on a given step
	SlowFactor float64 `json:"slowFactor"` // how much slower a slow GPU is
	Jitter     float64 `json:"jitter"`     // mean extra time per GPU per step, as a fraction of Base
	Base       float64 `json:"base"`       // seconds of compute per step
	Sync       float64 `json:"sync"`       // seconds to synchronise after each step
	GPUMTBF    float64 `json:"gpuMtbf"`    // hours between failures of one GPU
	Days       float64 `json:"days"`       // length of the simulated run
	Seed       uint64  `json:"seed"`
}

// LlamaGPUMTBF is the per-GPU mean time between failures implied by 419
// interruptions in 54 days on 16,384 GPUs.
const LlamaGPUMTBF = 54 * 24 * 16384 / 419.0

// BackupShare is how many extra GPUs backup mode runs.
const BackupShare = 0.02

func Defaults() Params {
	return Params{
		GPUs: 16384, Backup: false, Interval: 120, CkptCost: 1, Restart: 5,
		SlowProb: 1e-4, SlowFactor: 1.5, Jitter: 0.01, Base: 1, Sync: 0.1,
		GPUMTBF: LlamaGPUMTBF, Days: 14, Seed: 9,
	}
}

func (p Params) validate() error {
	switch {
	case p.GPUs < 1 || p.GPUs > 1<<20:
		return fmt.Errorf("gpus out of range")
	case p.Interval < 0.5 || p.Interval > 7*24*60:
		return fmt.Errorf("interval out of range")
	case p.CkptCost <= 0 || p.CkptCost > 600 || p.Restart < 0 || p.Restart > 600:
		return fmt.Errorf("checkpoint or restart cost out of range")
	case p.SlowProb < 0 || p.SlowProb > 0.05 || p.SlowFactor < 1 || p.SlowFactor > 20:
		return fmt.Errorf("slow GPU settings out of range")
	case p.Jitter < 0 || p.Jitter > 1 || p.Base <= 0 || p.Sync < 0:
		return fmt.Errorf("step settings out of range")
	case p.GPUMTBF <= 0 || p.Days <= 0 || p.Days > 60:
		return fmt.Errorf("failure settings out of range")
	}
	// keep the timeline small: no more than ~25k checkpoints in a run
	if p.Days*24*60/(p.Interval+p.CkptCost) > 25000 {
		return fmt.Errorf("interval too short for a run this long")
	}
	return nil
}

// ClusterMTBF is the cluster's mean time between failures, in hours,
// counting backup GPUs (they fail too).
func (p Params) ClusterMTBF() float64 { return p.GPUMTBF / float64(p.GPUs+p.backups()) }

func (p Params) backups() int {
	if !p.Backup {
		return 0
	}
	return int(math.Ceil(BackupShare * float64(p.GPUs)))
}

// YoungDaly is the classic checkpoint interval sqrt(2 * cost * MTBF), minutes.
func (p Params) YoungDaly() float64 { return math.Sqrt(2 * p.CkptCost * p.ClusterMTBF() * 60) }

// ---- stragglers

// maxExp samples the largest of n exponential draws with the given mean,
// from the distribution of the maximum: P(max <= x) = (1 - e^(-x/m))^n.
func maxExp(r *rand.Rand, n int, mean float64) float64 {
	if n <= 0 || mean == 0 {
		return 0
	}
	u := r.Float64()
	for u == 0 {
		u = r.Float64()
	}
	return -mean * math.Log(-math.Expm1(math.Log(u)/float64(n)))
}

func poisson(r *rand.Rand, lambda float64) int {
	if lambda <= 0 {
		return 0
	}
	if lambda > 30 {
		return max(0, int(math.Round(lambda+math.Sqrt(lambda)*r.NormFloat64())))
	}
	l, k, prod := math.Exp(-lambda), 0, r.Float64()
	for prod > l {
		k++
		prod *= r.Float64()
	}
	return k
}

// Step is one training step as the page draws it.
type Step struct {
	Slow    int       `json:"slow"`    // slow GPUs this step (all of them, not just those shown)
	Waited  bool      `json:"waited"`  // the step had to wait for a slow GPU
	Compute float64   `json:"compute"` // seconds until the GPUs the step needs have finished
	End     float64   `json:"end"`     // compute + sync
	Finish  []float64 `json:"f"`       // finish time of each GPU shown
	Kind    []int     `json:"k"`       // 0 healthy, 1 slow and waited for, 2 slow and skipped (backup)
}

// step samples one step: its length in seconds and the number of slow GPUs.
func (p Params) step(r *rand.Rand) (dur float64, slow int, waited bool, healthyMax, slowMax float64) {
	b := p.backups()
	slow = poisson(r, float64(p.GPUs+b)*p.SlowProb)
	slow = min(slow, p.GPUs+b)
	healthyMax = p.Base * (1 + maxExp(r, p.GPUs, p.Jitter))
	need := slow - b // slow GPUs the step still has to wait for
	if need < 0 {
		need = 0
	}
	compute := healthyMax
	if need > 0 {
		slowMax = p.Base * p.SlowFactor * (1 + maxExp(r, need, p.Jitter))
		if slowMax > compute {
			compute = slowMax
			waited = true
		}
	}
	return compute + p.Sync, slow, waited, healthyMax, slowMax
}

// StepEfficiency is the ideal step (no jitter, no slow GPUs) divided by the
// average simulated step, times the share of GPUs doing useful work (backup
// GPUs cost money too).
func (p Params) StepEfficiency(r *rand.Rand, samples int) (eff, meanStep, slowShare float64) {
	var sum float64
	waited := 0
	for i := 0; i < samples; i++ {
		d, _, w, _, _ := p.step(r)
		sum += d
		if w {
			waited++
		}
	}
	meanStep = sum / float64(samples)
	ideal := p.Base + p.Sync
	eff = ideal / meanStep * float64(p.GPUs) / float64(p.GPUs+p.backups())
	return eff, meanStep, float64(waited) / float64(samples)
}

// steps draws a few steps for the page, showing at most `show` GPUs: every
// slow GPU (up to a quarter of the cells) and the slowest healthy one are
// always among those shown; the rest are typical healthy GPUs.
func (p Params) steps(r *rand.Rand, count, show int) []Step {
	b := p.backups()
	cells := min(show, p.GPUs+b)
	out := make([]Step, 0, count)
	for i := 0; i < count; i++ {
		dur, slow, waited, hmax, _ := p.step(r)
		s := Step{Slow: slow, Waited: waited, End: r4(dur), Compute: r4(dur - p.Sync)}
		kinds := make([]int, cells)
		fin := make([]float64, cells)
		shownSlow := min(slow, cells/4)
		// the slow ones: the slowest `need` are waited for, the rest skipped
		need := slow - b
		for k := 0; k < shownSlow; k++ {
			kinds[k] = 1
			if need <= 0 || k >= need {
				kinds[k] = 2
			}
			fin[k] = p.Base * p.SlowFactor * (1 + r.ExpFloat64()*p.Jitter)
		}
		// make the slowest waited-for one match the step's compute time
		if waited && shownSlow > 0 {
			fin[0] = dur - p.Sync
		}
		if shownSlow < cells {
			fin[shownSlow] = hmax
			// typical healthy GPUs: exponential jitter, truncated at the max
			cap := (hmax/p.Base - 1)
			for k := shownSlow + 1; k < cells; k++ {
				var j float64
				if p.Jitter > 0 && cap > 0 {
					u := r.Float64()
					j = -p.Jitter * math.Log(1-u*(1-math.Exp(-cap/p.Jitter)))
				}
				fin[k] = p.Base * (1 + j)
			}
		}
		// shuffle so the special cells land anywhere
		perm := r.Perm(cells)
		s.Finish = make([]float64, cells)
		s.Kind = make([]int, cells)
		for k, j := range perm {
			s.Finish[j] = r4(fin[k])
			s.Kind[j] = kinds[k]
		}
		out = append(out, s)
	}
	return out
}

// ---- failures and checkpoints

// Segment kinds on the timeline.
const (
	SegCompute = iota // training whose result was kept
	SegCkpt           // writing a checkpoint
	SegLost           // training thrown away by a failure
	SegRestart        // recovering after a failure
)

// Timeline is one simulated run, in hours.
type Timeline struct {
	Segs     [][3]float64 `json:"segs"`  // [kind, start, end]
	Failures []float64    `json:"fails"` // when each failure happened
}

type runStats struct {
	useful, ckpt, lost, restart float64 // hours
	failures                    int
}

// run simulates checkpointing and failures over the run. Failures arrive as
// a Poisson process with the cluster's MTBF, but not during a restart.
func (p Params) run(r *rand.Rand, record bool) (runStats, Timeline) {
	T := p.Days * 24
	tau, delta, R, M := p.Interval/60, p.CkptCost/60, p.Restart/60, p.ClusterMTBF()
	var st runStats
	var tl Timeline
	add := func(kind int, a, b float64) {
		if record && b > a {
			tl.Segs = append(tl.Segs, [3]float64{float64(kind), r4(a), r4(b)})
		}
	}
	t := 0.0
	for t < T {
		fail := t + r.ExpFloat64()*M
		since := t            // start of work not yet saved
		first := len(tl.Segs) // first segment of that work
		failed := false
		for !failed && t < T {
			end := t + tau
			if fail <= end && fail < T { // fails while training
				add(SegCompute, t, fail)
				t, failed = fail, true
				break
			}
			if end >= T { // the run ends mid-interval; that work counts
				add(SegCompute, t, T)
				st.useful += T - t
				t = T
				break
			}
			add(SegCompute, t, end)
			t = end
			ck := t + delta
			if fail <= ck && fail < T { // fails while writing the checkpoint
				add(SegCkpt, t, fail)
				st.ckpt += fail - t
				t, failed = fail, true
				break
			}
			if ck >= T {
				add(SegCkpt, t, T)
				st.ckpt += T - t
				st.useful += tau
				t = T
				break
			}
			add(SegCkpt, t, ck)
			st.ckpt += delta
			st.useful += tau
			t = ck
			since, first = t, len(tl.Segs)
		}
		if !failed {
			break
		}
		// everything trained since the last checkpoint is lost
		st.failures++
		if record {
			for i := first; i < len(tl.Segs); i++ {
				if tl.Segs[i][0] == SegCompute {
					tl.Segs[i][0] = SegLost
				}
			}
			tl.Failures = append(tl.Failures, r4(t))
		}
		// training since the last checkpoint is thrown away (a partial
		// checkpoint write is already counted in st.ckpt)
		st.lost += t - since
		rEnd := math.Min(t+R, T)
		add(SegRestart, t, rEnd)
		st.restart += rEnd - t
		t = rEnd
	}
	return st, tl
}

// CkptEfficiency is the expected share of wall time that ends up as kept
// training, for exponential failures with no failures during restarts: a
// segment of length a = interval + cost takes (MTBF + R)(e^(a/MTBF) - 1) on
// average.
func (p Params) CkptEfficiency(intervalMin float64) float64 {
	tau, delta, R, M := intervalMin/60, p.CkptCost/60, p.Restart/60, p.ClusterMTBF()
	return tau / ((M + R) * math.Expm1((tau+delta)/M))
}

// BestInterval finds the interval (minutes) that maximises CkptEfficiency.
func (p Params) BestInterval() float64 {
	lo, hi := math.Log(0.5), math.Log(7*24*60.0)
	for i := 0; i < 100; i++ {
		a, b := lo+(hi-lo)/3, hi-(hi-lo)/3
		if p.CkptEfficiency(math.Exp(a)) < p.CkptEfficiency(math.Exp(b)) {
			lo = a
		} else {
			hi = b
		}
	}
	return math.Exp((lo + hi) / 2)
}

// ---- the page

// Stats summarise one policy.
type Stats struct {
	Policy     string  `json:"policy"`
	Label      string  `json:"label"`
	Interval   float64 `json:"interval"` // minutes
	Backup     bool    `json:"backup"`
	Failures   int     `json:"failures"`   // in the simulated run
	CkptShare  float64 `json:"ckptShare"`  // wall time writing checkpoints
	LostShare  float64 `json:"lostShare"`  // wall time redoing lost work or restarting
	CkptEff    float64 `json:"ckptEff"`    // kept training / wall time, simulated
	CkptEffExp float64 `json:"ckptEffExp"` // the same, expected value
	MeanStep   float64 `json:"meanStep"`   // seconds
	SlowShare  float64 `json:"slowShare"`  // steps that waited for a slow GPU
	StepEff    float64 `json:"stepEff"`    // ideal step / mean step (x useful GPU share)
	Goodput    float64 `json:"goodput"`    // CkptEff * StepEff
}

// CurvePoint is one point of goodput against checkpoint interval.
type CurvePoint struct {
	Interval float64 `json:"min"`
	Eff      float64 `json:"eff"`
}

// ScalePoint is step efficiency at one cluster size.
type ScalePoint struct {
	GPUs   int     `json:"n"`
	Plain  float64 `json:"plain"`
	Backup float64 `json:"backup"`
}

type Derived struct {
	ClusterMTBF float64 `json:"clusterMtbf"` // hours
	YoungDaly   float64 `json:"youngDaly"`   // minutes
	Best        float64 `json:"best"`        // minutes, from the exact expectation
	Backups     int     `json:"backups"`
	Shown       int     `json:"shown"` // GPUs drawn in the step view
}

type Result struct {
	Params   Params       `json:"params"`
	Derived  Derived      `json:"derived"`
	Stats    []Stats      `json:"stats"`
	Curve    []CurvePoint `json:"curve"`
	Scale    []ScalePoint `json:"scale"`
	Steps    []Step       `json:"steps"`
	Timeline Timeline     `json:"timeline"`
}

const stepSamples = 20000

func (p Params) stats(policy, label string) Stats {
	r := rand.New(rand.NewPCG(p.Seed, 2))
	eff, mean, slow := p.StepEfficiency(r, stepSamples)
	rs, _ := p.run(rand.New(rand.NewPCG(p.Seed, 3)), false)
	T := p.Days * 24
	ce := rs.useful / T
	return Stats{
		Policy: policy, Label: label, Interval: p.Interval, Backup: p.Backup,
		Failures: rs.failures, CkptShare: rs.ckpt / T, LostShare: (rs.lost + rs.restart) / T,
		CkptEff: ce, CkptEffExp: p.CkptEfficiency(p.Interval),
		MeanStep: mean, SlowShare: slow, StepEff: eff, Goodput: ce * eff,
	}
}

func fmtMin(m float64) string {
	if m >= 90 {
		return fmt.Sprintf("%.1f h", m/60)
	}
	if m >= 10 {
		return fmt.Sprintf("%.0f min", m)
	}
	return fmt.Sprintf("%.1f min", m)
}

// Run is the page's entry point.
func Run(params json.RawMessage) (any, error) {
	p := Defaults()
	if err := registry.Decode(params, &p); err != nil {
		return nil, err
	}
	if err := p.validate(); err != nil {
		return nil, err
	}
	plain := p
	plain.Backup = false
	yd := plain.YoungDaly()
	res := Result{Params: p, Derived: Derived{
		ClusterMTBF: p.ClusterMTBF(), YoungDaly: yd, Best: plain.BestInterval(), Backups: p.backups(),
	}}

	// the rows: the same run, checkpointing too often, at Young/Daly, too
	// rarely; Young/Daly with backup GPUs; and the page's own settings
	rows := []struct {
		key, label string
		interval   float64
		backup     bool
	}{
		{"often", "Too often: every " + fmtMin(yd/6), yd / 6, false},
		{"yd", "Young–Daly: every " + fmtMin(yd), yd, false},
		{"rare", "Too rarely: every " + fmtMin(yd*6), yd * 6, false},
		{"yd-backup", "Young–Daly + 2% backup GPUs", yd, true},
		{"yours", "Your settings", p.Interval, p.Backup},
	}
	for _, row := range rows {
		q := p
		q.Interval, q.Backup = math.Max(0.5, row.interval), row.backup
		if err := q.validate(); err != nil {
			return nil, fmt.Errorf("%s: %w", row.key, err)
		}
		res.Stats = append(res.Stats, q.stats(row.key, row.label))
	}

	// goodput against interval, from the exact expectation
	for i := 0; i <= 60; i++ {
		m := 0.5 * math.Pow(2880/0.5, float64(i)/60) // 30 s … 2 days
		res.Curve = append(res.Curve, CurvePoint{Interval: r4(m), Eff: r4(p.CkptEfficiency(m))})
	}
	// step efficiency against cluster size
	for n := 8; n <= 16384; n *= 2 {
		q := p
		q.GPUs, q.Backup = n, false
		a, _, _ := q.StepEfficiency(rand.New(rand.NewPCG(p.Seed, uint64(n))), 4000)
		q.Backup = true
		b, _, _ := q.StepEfficiency(rand.New(rand.NewPCG(p.Seed, uint64(n))), 4000)
		res.Scale = append(res.Scale, ScalePoint{GPUs: n, Plain: r4(a), Backup: r4(b)})
	}
	res.Derived.Shown = min(192, p.GPUs+p.backups())
	res.Steps = p.steps(rand.New(rand.NewPCG(p.Seed, 4)), 24, 192)
	_, res.Timeline = p.run(rand.New(rand.NewPCG(p.Seed, 3)), true)
	return res, nil
}

func r4(x float64) float64 { return math.Round(x*1e4) / 1e4 }

// Report is the terminal table.
func Report() string {
	out, _ := Run(nil)
	res := out.(Result)
	p, d := res.Params, res.Derived
	var b strings.Builder
	fmt.Fprintf(&b, "%d GPUs, one failure every %.1f h on average, checkpoint %.0f min, restart %.0f min, %.0f days\n", p.GPUs, d.ClusterMTBF, p.CkptCost, p.Restart, p.Days)
	fmt.Fprintf(&b, "Young–Daly interval %.1f min; exact best %.1f min\n\n", d.YoungDaly, d.Best)
	fmt.Fprintf(&b, "%-34s %8s %6s %8s %8s %9s %8s %8s\n", "policy", "every", "fails", "ckpt", "lost", "kept", "steps", "goodput")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-34s %8s %6d %7.1f%% %7.1f%% %8.1f%% %7.1f%% %7.1f%%\n", s.Label, fmtMin(s.Interval), s.Failures, s.CkptShare*100, s.LostShare*100, s.CkptEff*100, s.StepEff*100, s.Goodput*100)
	}
	fmt.Fprintf(&b, "\nstep efficiency by cluster size (waiting for every GPU / with 2%% backups):\n")
	for _, s := range res.Scale {
		fmt.Fprintf(&b, "  %6d GPUs  %5.1f%%  %5.1f%%\n", s.GPUs, s.Plain*100, s.Backup*100)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "straggler", Title: "The one slow GPU", Run: Run, Report: Report})
}
