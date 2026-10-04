package batching

import (
	"encoding/json"
	"testing"
)

func byPolicy(t *testing.T, q string) map[string]Stats {
	t.Helper()
	out, err := Run(json.RawMessage(q))
	if err != nil {
		t.Fatal(err)
	}
	m := map[string]Stats{}
	for _, s := range out.(Result).Stats {
		m[s.Policy] = s
	}
	return m
}

// The page's headline: at the default load, static batching leaves seats
// empty while people wait, and everyone waits far longer for it.
func TestStaticWastesSeatsAndTime(t *testing.T) {
	s := byPolicy(t, "")
	st, co := s["static"], s["continuous"]
	t.Logf("static: ttft %.1fs lat %.1fs wasted %.0f%%; continuous: ttft %.1fs lat %.1fs", st.TTFTMean, st.LatencyMean, st.Wasted*100, co.TTFTMean, co.LatencyMean)
	if st.Wasted < 0.3 {
		t.Fatalf("static wasted only %.2f of seat time", st.Wasted)
	}
	if st.TTFTMean < 10*co.TTFTMean {
		t.Fatalf("first token: static %.2fs, continuous %.2fs", st.TTFTMean, co.TTFTMean)
	}
	if st.LatencyMean < 3*co.LatencyMean {
		t.Fatalf("latency: static %.2fs, continuous %.2fs", st.LatencyMean, co.LatencyMean)
	}
}

// Push the load up and continuous batching keeps up where static can't.
func TestContinuousCarriesMore(t *testing.T) {
	s := byPolicy(t, `{"rate":2}`)
	if s["continuous"].Throughput < 1.5*s["static"].Throughput {
		t.Fatalf("throughput at 2 req/s: continuous %.0f, static %.0f", s["continuous"].Throughput, s["static"].Throughput)
	}
}

// Continuous batching never leaves a seat empty while someone is queued.
func TestContinuousNeverWastesASeat(t *testing.T) {
	for _, q := range []string{"", `{"rate":3}`, `{"slots":2,"spread":1.8}`} {
		if w := byPolicy(t, q)["continuous"].Wasted; w != 0 {
			t.Fatalf("%s: continuous wasted %.4f", q, w)
		}
	}
}

// Every request writes exactly its reply, in order, and no seat holds two
// requests at once.
func TestTraceIsConsistent(t *testing.T) {
	for _, pol := range Policies {
		p := Defaults()
		p.Policy = pol.Name
		res, err := Simulate(p)
		if err != nil {
			t.Fatal(err)
		}
		bySlot := map[int][]Req{}
		for _, r := range res.Trace {
			if !(r.T <= r.Start && r.Start < r.First && r.First <= r.End) {
				t.Fatalf("%s: out of order %+v", pol.Name, r)
			}
			// tokens written = steps the request was in
			n := 0
			for _, st := range res.Steps {
				if st.S >= r.Start && st.E <= r.End+1e-9 {
					n++
				}
			}
			if n != r.Out {
				t.Fatalf("%s: request wrote %d tokens in %d steps", pol.Name, r.Out, n)
			}
			bySlot[r.Slot] = append(bySlot[r.Slot], r)
		}
		for s, rs := range bySlot {
			for i := range rs {
				for j := i + 1; j < len(rs); j++ {
					if rs[i].Start < rs[j].End && rs[j].Start < rs[i].End {
						t.Fatalf("%s: seat %d held two requests", pol.Name, s)
					}
				}
			}
		}
	}
}

func TestDeterministic(t *testing.T) {
	a, _ := Run(nil)
	b, _ := Run(nil)
	ja, _ := json.Marshal(a)
	jb, _ := json.Marshal(b)
	if string(ja) != string(jb) {
		t.Fatal("same seed, different runs")
	}
}

func TestRejectsBadParams(t *testing.T) {
	if _, err := Run(json.RawMessage(`{"rate":0}`)); err == nil {
		t.Fatal("rate 0 accepted")
	}
	if _, err := Run(json.RawMessage(`{"policy":"nope"}`)); err == nil {
		t.Fatal("unknown policy accepted")
	}
}
