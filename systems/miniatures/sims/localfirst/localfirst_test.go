package localfirst

import (
	"math/rand/v2"
	"testing"
	"unicode/utf8"
)

// randomEdit makes a small random edit on d.
func randomEdit(r *rand.Rand, d *Doc) {
	n := utf8.RuneCountInString(d.Text())
	at := r.IntN(n + 1)
	del := 0
	if n > at && r.IntN(3) == 0 {
		del = 1 + r.IntN(min(3, n-at))
	}
	ins := ""
	for k := r.IntN(4); k > 0; k-- {
		ins += string(rune('a' + r.IntN(26)))
	}
	if _, err := d.Edit(at, del, ins); err != nil {
		panic(err)
	}
}

// Random concurrent edits on 2–3 phones with random partial syncs in
// between; once everyone has everything, every phone shows the same text.
func TestConvergence(t *testing.T) {
	for seed := uint64(0); seed < 300; seed++ {
		r := rand.New(rand.NewPCG(seed, 9))
		n := 2 + r.IntN(2)
		docs := make([]*Doc, n)
		for i := range docs {
			docs[i] = NewDoc(i, "hello world")
		}
		for step := 0; step < 60; step++ {
			if r.IntN(4) == 0 {
				a, b := r.IntN(n), r.IntN(n)
				if a != b {
					docs[b].SyncFrom(docs[a])
				}
				continue
			}
			randomEdit(r, docs[r.IntN(n)])
		}
		// final sync in a random order, twice round so everything spreads
		for round := 0; round < 2; round++ {
			for _, k := range r.Perm(n * n) {
				a, b := k/n, k%n
				if a != b {
					docs[b].SyncFrom(docs[a])
				}
			}
		}
		for i := 1; i < n; i++ {
			if docs[i].Text() != docs[0].Text() {
				t.Fatalf("seed %d: phone %d %q != phone 0 %q", seed, i, docs[i].Text(), docs[0].Text())
			}
		}
	}
}

// The same ops delivered in any order (missing references wait in the
// pending queue) give the same text.
func TestAnyDeliveryOrder(t *testing.T) {
	for seed := uint64(0); seed < 200; seed++ {
		r := rand.New(rand.NewPCG(seed, 3))
		a, b := NewDoc(0, "abc"), NewDoc(1, "abc")
		for i := 0; i < 25; i++ {
			randomEdit(r, a)
			randomEdit(r, b)
		}
		ops := append(append([]Op{}, a.log...), b.log...)
		want := ""
		for trial := 0; trial < 4; trial++ {
			d := NewDoc(2, "abc")
			for _, k := range r.Perm(len(ops)) {
				d.Receive(ops[k])
			}
			if len(d.pending) != 0 {
				t.Fatalf("seed %d: %d ops never applied", seed, len(d.pending))
			}
			if trial == 0 {
				want = d.Text()
			} else if d.Text() != want {
				t.Fatalf("seed %d: order changed the result: %q vs %q", seed, d.Text(), want)
			}
		}
	}
}

// Applying an op twice is harmless.
func TestIdempotent(t *testing.T) {
	a := NewDoc(0, "abc")
	ops, _ := a.Edit(1, 1, "XY")
	b := NewDoc(1, "abc")
	for _, op := range ops {
		b.Receive(op)
		b.Receive(op)
	}
	b.SyncFrom(a)
	if b.Text() != "aXYc" || a.Text() != "aXYc" {
		t.Fatalf("got %q / %q", a.Text(), b.Text())
	}
}

// A run typed in one go stays together, even when the other phone typed at
// the same spot.
func TestRunsDontInterleave(t *testing.T) {
	a, b := NewDoc(0, "fox"), NewDoc(1, "fox")
	a.Edit(0, 0, "sly ")
	b.Edit(0, 0, "small ")
	a.SyncFrom(b)
	b.SyncFrom(a)
	if got := a.Text(); got != b.Text() || (got != "sly small fox" && got != "small sly fox") {
		t.Fatalf("got %q and %q", a.Text(), b.Text())
	}
}

// The page's headline: in the example, last-writer-wins loses phone A's
// work and brings its deleted typo back; the CRDT keeps everything.
func TestExample(t *testing.T) {
	p := Defaults()
	p.Events = Demo()
	res, err := Simulate(p)
	if err != nil {
		t.Fatal(err)
	}
	if !res.Synced {
		t.Fatalf("phones differ after sync: %q / %q", res.Phones[0].Text, res.Phones[1].Text)
	}
	lww, crdt := res.Stats[0], res.Stats[1]
	if res.Winner != 1 {
		t.Fatalf("phone B edited last, winner %d", res.Winner)
	}
	if lww.Lost == 0 || lww.Back == 0 || lww.KeptTyped >= 1 {
		t.Fatalf("last writer wins should lose work: %+v", lww)
	}
	if lww.Text != "Teh quick brown small fox jumps over the lazy dog." {
		t.Fatalf("lww text %q", lww.Text)
	}
	for _, w := range []string{"The ", "sly ", "small ", "jumps"} {
		if !contains(crdt.Text, w) {
			t.Fatalf("CRDT result %q is missing %q", crdt.Text, w)
		}
	}
	if crdt.Text != res.Phones[0].Text {
		t.Fatalf("CRDT preview %q != phone text %q", crdt.Text, res.Phones[0].Text)
	}
}

func contains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}

func TestRejectsBadInput(t *testing.T) {
	p := Defaults()
	p.Events = []Event{{K: "edit", R: 0, At: 999, Ins: "x"}}
	if _, err := Simulate(p); err == nil {
		t.Fatal("expected out-of-range error")
	}
	p.Events = []Event{{K: "edit", R: 5}}
	if _, err := Simulate(p); err == nil {
		t.Fatal("expected bad phone error")
	}
}
