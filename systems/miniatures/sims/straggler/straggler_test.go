package straggler

import (
	"encoding/json"
	"math"
	"math/rand/v2"
	"testing"
)

func rows(t *testing.T, params string) map[string]Stats {
	t.Helper()
	out, err := Run(json.RawMessage(params))
	if err != nil {
		t.Fatal(err)
	}
	m := map[string]Stats{}
	for _, s := range out.(Result).Stats {
		m[s.Policy] = s
	}
	return m
}

// The default failure rate is the Llama 3 figure: one interruption every
// ~3.1 hours on 16,384 GPUs.
func TestClusterMTBFMatchesLlama3(t *testing.T) {
	got := Defaults().ClusterMTBF()
	if want := 54 * 24 / 419.0; math.Abs(got-want) > 1e-9 {
		t.Fatalf("cluster MTBF %.3f h, want %.3f h", got, want)
	}
}

// Checkpointing at the Young–Daly interval beats checkpointing 6x more often
// and 6x less often, in the simulated run and in expectation.
func TestYoungDalyBeatsBothSides(t *testing.T) {
	s := rows(t, "")
	for _, k := range []string{"often", "rare"} {
		if s["yd"].Goodput <= s[k].Goodput+0.05 {
			t.Errorf("Young–Daly %.3f vs %s %.3f", s["yd"].Goodput, k, s[k].Goodput)
		}
		if s["yd"].CkptEffExp <= s[k].CkptEffExp {
			t.Errorf("expected: Young–Daly %.3f vs %s %.3f", s["yd"].CkptEffExp, k, s[k].CkptEffExp)
		}
	}
}

// Young/Daly is a first-order approximation; it should land within 10% of
// the exact optimum at the defaults.
func TestYoungDalyNearExactOptimum(t *testing.T) {
	p := Defaults()
	if yd, best := p.YoungDaly(), p.BestInterval(); math.Abs(yd-best)/best > 0.1 {
		t.Fatalf("Young–Daly %.1f min, exact best %.1f min", yd, best)
	}
}

// The simulation agrees with the closed-form expectation over a long run.
func TestSimulationMatchesExpectation(t *testing.T) {
	p := Defaults()
	p.Days, p.Interval = 60, p.YoungDaly()
	var sum float64
	const runs = 8
	for seed := uint64(1); seed <= runs; seed++ {
		st, _ := p.run(rand.New(rand.NewPCG(seed, 3)), false)
		sum += st.useful / (p.Days * 24)
	}
	if got, want := sum/runs, p.CkptEfficiency(p.Interval); math.Abs(got-want) > 0.01 {
		t.Fatalf("simulated %.4f, expected %.4f", got, want)
	}
}

// Stragglers: at 8 GPUs a step is close to ideal; at 16,384 some GPU is slow
// most steps, and waiting for it costs over a fifth of the time. Backup GPUs
// win back most of it at scale but cost more than they save on 8 GPUs.
func TestStragglersGrowWithScale(t *testing.T) {
	out, _ := Run(nil)
	sc := out.(Result).Scale
	small, big := sc[0], sc[len(sc)-1]
	if small.GPUs != 8 || big.GPUs != 16384 {
		t.Fatalf("scale points %d..%d", small.GPUs, big.GPUs)
	}
	if small.Plain < 0.95 || big.Plain > 0.8 {
		t.Fatalf("step efficiency: 8 GPUs %.3f, 16384 GPUs %.3f", small.Plain, big.Plain)
	}
	if big.Backup < big.Plain+0.1 || small.Backup >= small.Plain {
		t.Fatalf("backups: 8 GPUs %.3f vs %.3f, 16384 GPUs %.3f vs %.3f", small.Backup, small.Plain, big.Backup, big.Plain)
	}
}

func TestMaxExpMatchesDistribution(t *testing.T) {
	// E[max of n Exp(1)] = H_n, the n-th harmonic number
	r := rand.New(rand.NewPCG(1, 1))
	n := 1000
	var sum float64
	for i := 0; i < 20000; i++ {
		sum += maxExp(r, n, 1)
	}
	h := 0.0
	for k := 1; k <= n; k++ {
		h += 1 / float64(k)
	}
	if got := sum / 20000; math.Abs(got-h) > 0.05 {
		t.Fatalf("mean max %.3f, want %.3f", got, h)
	}
}

func TestDeterministic(t *testing.T) {
	a, _ := json.Marshal(must(Run(nil)))
	b, _ := json.Marshal(must(Run(nil)))
	if string(a) != string(b) {
		t.Fatal("two runs with the same seed differ")
	}
}

// The timeline covers the whole run with no gaps or overlaps, and kept work
// never exceeds wall time.
func TestTimelineTilesTheRun(t *testing.T) {
	for _, iv := range []float64{3, 19, 120} {
		p := Defaults()
		p.Interval = iv
		st, tl := p.run(rand.New(rand.NewPCG(p.Seed, 3)), true)
		end := 0.0
		kept := 0.0
		for _, s := range tl.Segs {
			if math.Abs(s[1]-end) > 2e-4 || s[2] < s[1] {
				t.Fatalf("interval %v: segment %v after %v", iv, s, end)
			}
			end = s[2]
			if s[0] == SegCompute {
				kept += s[2] - s[1]
			}
		}
		if math.Abs(end-p.Days*24) > 2e-4 {
			t.Fatalf("interval %v: timeline ends at %v", iv, end)
		}
		if math.Abs(kept-st.useful) > 0.05 || st.useful > p.Days*24 {
			t.Fatalf("interval %v: kept %.3f vs useful %.3f", iv, kept, st.useful)
		}
		if len(tl.Failures) != st.failures {
			t.Fatalf("failures %d vs %d", len(tl.Failures), st.failures)
		}
	}
}

func TestRejectsBadParams(t *testing.T) {
	for _, bad := range []string{`{"gpus":0}`, `{"interval":0.01}`, `{"days":1000}`, `{"slowProb":2}`} {
		if _, err := Run(json.RawMessage(bad)); err == nil {
			t.Errorf("%s accepted", bad)
		}
	}
}

func must(v any, err error) any {
	if err != nil {
		panic(err)
	}
	return v
}
