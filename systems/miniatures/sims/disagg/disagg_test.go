package disagg

import (
	"reflect"
	"testing"
)

func byPolicy(t *testing.T, p Params) map[string]Stats {
	t.Helper()
	m := map[string]Stats{}
	for _, pol := range Policies {
		q := p
		q.Policy = pol.Name
		r, err := Simulate(q)
		if err != nil {
			t.Fatal(err)
		}
		m[pol.Name] = r.Stats[0]
	}
	return m
}

// The page's headline: on one GPU, long prompts freeze replies; split across
// GPUs, almost every request is on time.
func TestSeparateGPUsStreamSmoothly(t *testing.T) {
	p := Defaults()
	s := byPolicy(t, p)
	if s["colocated"].GapP90 <= p.SLOPause {
		t.Fatalf("colocated pause p90 %.3fs should exceed the %.3fs target", s["colocated"].GapP90, p.SLOPause)
	}
	if s["colocated"].Goodput > 0.2 {
		t.Fatalf("colocated on time %.2f, expected under 0.2", s["colocated"].Goodput)
	}
	if s["disaggregated"].Goodput < 0.95 {
		t.Fatalf("separate GPUs on time %.2f, expected at least 0.95", s["disaggregated"].Goodput)
	}
	if s["disaggregated"].Goodput <= s["chunked"].Goodput {
		t.Fatalf("separate %.2f should beat chunked %.2f at the default load", s["disaggregated"].Goodput, s["chunked"].Goodput)
	}
	// averages hide it: colocated's typical gap is still fine
	if s["colocated"].TPOTP50 > p.SLOTPOT {
		t.Fatalf("colocated median gap %.3fs; the point is that the average looks fine", s["colocated"].TPOTP50)
	}
}

// The split matters: too few prompt readers and first tokens queue; too few
// writers and every reply slows.
func TestTheSplitHasToFit(t *testing.T) {
	for _, pg := range []int{1, 3} {
		p := Defaults()
		p.PrefillGPUs = pg
		r, err := Simulate(p)
		if err != nil {
			t.Fatal(err)
		}
		if g := r.Stats[0].Goodput; g > 0.5 {
			t.Fatalf("%d prompt GPUs: on time %.2f, expected the wrong split to fail", pg, g)
		}
	}
}

func TestDeterministic(t *testing.T) {
	a, _ := Simulate(Defaults())
	b, _ := Simulate(Defaults())
	if !reflect.DeepEqual(a, b) {
		t.Fatal("same seed, different result")
	}
}

func TestInvariants(t *testing.T) {
	for _, pol := range Policies {
		p := Defaults()
		p.Policy = pol.Name
		r, err := Simulate(p)
		if err != nil {
			t.Fatal(err)
		}
		// a GPU never runs two iterations at once
		last := map[float64]float64{}
		for _, it := range r.Iters {
			if it[1] < last[it[0]]-1e-3 {
				t.Fatalf("%s: GPU %v overlaps at %v", pol.Name, it[0], it[1])
			}
			last[it[0]] = it[1] + it[2]
		}
		for _, q := range r.Reqs {
			if q.End >= 0 && (q.First < q.T || q.End < q.First) {
				t.Fatalf("%s: times out of order %+v", pol.Name, q)
			}
		}
		// sampled requests produce exactly their reply length, in order
		for _, s := range r.Samples {
			q := r.Reqs[s.ID]
			if q.End >= 0 && len(s.Tokens) != q.Out {
				t.Fatalf("%s: request %d made %d tokens, wanted %d", pol.Name, s.ID, len(s.Tokens), q.Out)
			}
			for i := 1; i < len(s.Tokens); i++ {
				if s.Tokens[i] < s.Tokens[i-1] {
					t.Fatalf("%s: tokens out of order", pol.Name)
				}
			}
		}
	}
}

func TestRejectsBadParams(t *testing.T) {
	p := Defaults()
	p.PrefillGPUs = p.GPUs
	if _, err := Simulate(p); err == nil {
		t.Fatal("all GPUs reading prompts should be rejected")
	}
	p = Defaults()
	p.Rate = 1e6
	if _, err := Simulate(p); err == nil {
		t.Fatal("huge rate should be rejected")
	}
}
