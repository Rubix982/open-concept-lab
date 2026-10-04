package herd

import (
	"encoding/json"
	"math"
	"testing"
)

func run(t *testing.T, params string) Result {
	t.Helper()
	out, err := Run(json.RawMessage(params))
	if err != nil {
		t.Fatal(err)
	}
	return out.(Result)
}

func byPolicy(r Result) map[string]Stats {
	m := map[string]Stats{}
	for _, s := range r.Stats {
		m[s.Policy] = s
	}
	return m
}

// The page's headline: retrying immediately hammers a dead API; the breaker
// sends about one probe a second.
func TestRetryStormDuringOutage(t *testing.T) {
	s := byPolicy(run(t, "{}"))
	if s["immediate"].OutageCalls < 5000 {
		t.Fatalf("immediate retry sent only %d calls during the outage", s["immediate"].OutageCalls)
	}
	if s["shared"].OutageCalls > int(Defaults().OutageLen)+2 {
		t.Fatalf("breaker sent %d calls during a %.0fs outage", s["shared"].OutageCalls, Defaults().OutageLen)
	}
	for _, p := range []string{"fixed", "exponential", "jitter"} {
		if s[p].OutageCalls >= s["immediate"].OutageCalls || s[p].OutageCalls <= s["shared"].OutageCalls {
			t.Fatalf("%s outage calls %d not between breaker and immediate", p, s[p].OutageCalls)
		}
	}
}

// Backing off means sleeping through the API's return; the breaker resumes
// as soon as a probe gets through.
func TestBackoffOversleeps(t *testing.T) {
	s := byPolicy(run(t, "{}"))
	if s["shared"].CatchUp >= s["exponential"].CatchUp || s["shared"].CatchUp >= s["jitter"].CatchUp {
		t.Fatalf("catch-up: breaker %.1fs, exponential %.1fs, jitter %.1fs", s["shared"].CatchUp, s["exponential"].CatchUp, s["jitter"].CatchUp)
	}
	if s["shared"].Rejected != 0 {
		t.Fatalf("shared budget got %d 429s", s["shared"].Rejected)
	}
}

// Without jitter the fleet's first retries go out in synchronised waves with
// silent gaps between them; jitter evens them out.
func TestJitterSmoothsTheStartupWaves(t *testing.T) {
	cv := func(policy string) float64 {
		r := run(t, `{"policy":"`+policy+`"}`)
		xs := r.Bins[2:20]
		var m, v float64
		for _, b := range xs {
			m += float64(b.Attempts)
		}
		m /= float64(len(xs))
		for _, b := range xs {
			v += (float64(b.Attempts) - m) * (float64(b.Attempts) - m)
		}
		return math.Sqrt(v/float64(len(xs))) / m
	}
	if e, j := cv("exponential"), cv("jitter"); e < 1.5*j {
		t.Fatalf("startup burstiness: exponential %.2f, jitter %.2f", e, j)
	}
}

// The API never hands out more tokens than its bucket allows.
func TestNeverOverTheLimit(t *testing.T) {
	for _, p := range Policies {
		r := run(t, `{"policy":"`+p.Name+`"}`)
		cap := r.Rate * r.Params.BurstSeconds
		var cum float64
		for k, b := range r.Bins {
			cum += float64(b.Tokens)
			if limit := cap + r.Rate*float64(k+1)*r.BinW; cum > limit+1 {
				t.Fatalf("%s: %.0f tokens by %.2fs, limit %.0f", p.Name, cum, float64(k+1)*r.BinW, limit)
			}
		}
	}
}

func TestDeterministic(t *testing.T) {
	a, _ := json.Marshal(run(t, `{"policy":"jitter"}`))
	b, _ := json.Marshal(run(t, `{"policy":"jitter"}`))
	if string(a) != string(b) {
		t.Fatal("same seed, different runs")
	}
}

func TestNoOutageAndBounds(t *testing.T) {
	r := run(t, `{"outageLen":0}`)
	for _, s := range r.Stats {
		if s.OutageCalls != 0 || s.Completed == 0 {
			t.Fatalf("%s: outage calls %d, completed %d", s.Policy, s.OutageCalls, s.Completed)
		}
	}
	if _, err := Run(json.RawMessage(`{"agents":100000}`)); err == nil {
		t.Fatal("expected an error for 100,000 agents")
	}
}

func TestTraceSize(t *testing.T) {
	for _, p := range Policies {
		b, _ := json.Marshal(run(t, `{"policy":"`+p.Name+`","agents":300}`))
		if len(b) > 1_500_000 {
			t.Fatalf("%s: %d bytes", p.Name, len(b))
		}
	}
}
