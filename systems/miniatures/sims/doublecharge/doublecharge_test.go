package doublecharge

import "testing"

func byPolicy(t *testing.T, params string) map[string]Stats {
	t.Helper()
	var raw []byte
	if params != "" {
		raw = []byte(params)
	}
	out, err := Run(raw)
	if err != nil {
		t.Fatal(err)
	}
	m := map[string]Stats{}
	for _, s := range out.(Result).Stats {
		m[s.Policy] = s
	}
	return m
}

// The page's headline, at the default settings: without a key retries charge
// people twice; a key checked-then-inserted halves that but doesn't end it;
// a key claimed atomically ends it.
func TestHeadline(t *testing.T) {
	s := byPolicy(t, "")
	if s["no-key"].Twice < 40 {
		t.Fatalf("no key: only %d double charges", s["no-key"].Twice)
	}
	if s["check-insert"].Twice == 0 || s["check-insert"].Twice >= s["no-key"].Twice {
		t.Fatalf("check-insert: %d double charges (no key %d)", s["check-insert"].Twice, s["no-key"].Twice)
	}
	if s["atomic"].Twice != 0 || s["atomic"].Extra != 0 {
		t.Fatalf("atomic: %d double charges", s["atomic"].Twice)
	}
}

// The check-then-insert duplicates are all the race: a retry reaching the
// server while an earlier attempt is still being processed.
func TestCheckInsertDuplicatesAreTheRace(t *testing.T) {
	out, _ := Run([]byte(`{"policy":"check-insert"}`))
	for _, task := range out.(Result).Trace {
		if task.Charges < 2 {
			continue
		}
		raced := false
		for i, a := range task.Attempts {
			for _, b := range task.Attempts[i+1:] {
				if a.Charged && b.Charged && b.Arrive < a.Done {
					raced = true
				}
			}
		}
		if !raced {
			t.Fatalf("task %d charged %d times without overlapping attempts", task.ID, task.Charges)
		}
	}
}

// Whatever the network does, the atomic claim never charges twice, and a
// task is only ever uncharged if no request reached the server.
func TestAtomicNeverChargesTwice(t *testing.T) {
	for seed := uint64(1); seed <= 40; seed++ {
		p := Defaults()
		p.Seed, p.Loss, p.Slow, p.Timeout, p.Tries = seed, 0.3, 0.4, 0.5, 6
		res, err := Simulate(p)
		if err != nil {
			t.Fatal(err)
		}
		for _, task := range res.Trace {
			if task.Charges > 1 {
				t.Fatalf("seed %d task %d charged %d times", seed, task.ID, task.Charges)
			}
			arrived := false
			for _, a := range task.Attempts {
				arrived = arrived || a.Arrive >= 0
			}
			if arrived != (task.Charges == 1) {
				t.Fatalf("seed %d task %d: arrived %v but charged %d", seed, task.ID, arrived, task.Charges)
			}
		}
	}
}

// With no retries there are no duplicates, but lost requests go unpaid: the
// other way to fail.
func TestOneTryNeverDuplicatesButLosesSome(t *testing.T) {
	s := byPolicy(t, `{"tries":1}`)
	if s["no-key"].Twice != 0 {
		t.Fatalf("one try still double-charged %d", s["no-key"].Twice)
	}
	if s["no-key"].Never == 0 {
		t.Fatal("one try lost no purchases")
	}
}

func TestDeterministic(t *testing.T) {
	a, _ := Simulate(Defaults())
	b, _ := Simulate(Defaults())
	if a.Stats[0] != b.Stats[0] || len(a.Trace) != len(b.Trace) {
		t.Fatal("not deterministic")
	}
}

func TestRejectsBadParams(t *testing.T) {
	for _, bad := range []string{`{"tasks":0}`, `{"timeout":0.1}`, `{"tries":50}`, `{"policy":"maybe"}`} {
		if _, err := Run([]byte(bad)); err == nil {
			t.Fatalf("accepted %s", bad)
		}
	}
}
