// Package localfirst: two phones edit the same note offline, then sync.
//
// Each phone keeps its own copy of the text as a sequence CRDT — RGA, the
// Replicated Growable Array (Roh, Jeong, Kim and Lee, 2011). Every character
// gets an id that never changes: (counter, phone). Typing a character
// records "insert this, right after the character with id X"; deleting one
// records "hide the character with id X" — it stays in the list as a
// tombstone so later edits can still point at it. When two phones insert at
// the same spot without seeing each other, the character with the larger id
// goes first, and since every phone applies the same rule, every phone ends
// up with the same text no matter what order the edits arrive in.
//
// The comparison is what a simpler app would do: keep whole documents and,
// on sync, let the copy that was saved last replace the other ("last writer
// wins"). Everything the other phone did offline is lost, and its deletions
// come back.
//
// The page sends the whole history each time — edits by index into a phone's
// visible text, and syncs from one phone to another — and Run replays it from
// the start. Histories are small, so this stays fast.
package localfirst

import (
	"encoding/json"
	"fmt"
	"strings"
	"unicode/utf8"

	"miniatures/sims/registry"
)

// ---- the CRDT

// ID names one character forever. Base text uses phone -1.
type ID struct {
	C int `json:"c"` // Lamport counter
	R int `json:"r"` // phone that typed it
}

// less orders ids: the larger counter wins, then the larger phone number.
func (a ID) less(b ID) bool {
	if a.C != b.C {
		return a.C < b.C
	}
	return a.R < b.R
}

var head = ID{} // "insert at the start"

// Op is one character-level change.
type Op struct {
	ID  ID   `json:"id"`  // the new character (insert) or the op's own id (delete)
	Ref ID   `json:"ref"` // insert after this character; head for the start
	Ch  rune `json:"ch"`
	Del bool `json:"del"` // delete: hide character Ref
}

type elem struct {
	id      ID
	ch      rune
	deleted bool
}

// Doc is one phone's copy.
type Doc struct {
	Phone   int
	clock   int
	elems   []elem
	index   map[ID]int // id -> position in elems; rebuilt lazily
	seen    map[ID]bool
	log     []Op // every op applied here, in the order applied (causal)
	pending []Op // ops waiting for the character they refer to
}

// NewDoc starts a phone's copy from the shared base text.
func NewDoc(phone int, base string) *Doc {
	d := &Doc{Phone: phone, seen: map[ID]bool{}}
	prev := head
	for i, ch := range []rune(base) {
		id := ID{C: i + 1, R: -1}
		d.integrate(Op{ID: id, Ref: prev, Ch: ch})
		prev = id
	}
	d.log = nil // the base isn't anyone's edit
	return d
}

func (d *Doc) pos(id ID) int {
	if id == head {
		return -1
	}
	if d.index == nil {
		d.index = make(map[ID]int, len(d.elems))
		for i, e := range d.elems {
			d.index[e.id] = i
		}
	}
	if i, ok := d.index[id]; ok {
		return i
	}
	return -2
}

func (d *Doc) has(id ID) bool { return id == head || d.pos(id) >= 0 }

// integrate applies an op whose reference is present. Applying the same op
// twice changes nothing.
func (d *Doc) integrate(op Op) {
	if d.seen[op.ID] {
		return
	}
	d.seen[op.ID] = true
	if op.ID.C > d.clock {
		d.clock = op.ID.C
	}
	d.log = append(d.log, op)
	if op.Del {
		d.elems[d.pos(op.Ref)].deleted = true
		return
	}
	i := d.pos(op.Ref) + 1
	// skip characters inserted at the same spot with larger ids (and,
	// because their own followers have larger ids still, those too)
	for i < len(d.elems) && op.ID.less(d.elems[i].id) {
		i++
	}
	d.elems = append(d.elems, elem{})
	copy(d.elems[i+1:], d.elems[i:])
	d.elems[i] = elem{id: op.ID, ch: op.Ch}
	d.index = nil
}

// Receive applies an op from anywhere, holding it back until the character it
// refers to has arrived.
func (d *Doc) Receive(op Op) {
	d.pending = append(d.pending, op)
	for progress := true; progress; {
		progress = false
		rest := d.pending[:0]
		for _, p := range d.pending {
			if d.seen[p.ID] {
				progress = true
				continue
			}
			if d.has(p.Ref) {
				d.integrate(p)
				progress = true
			} else {
				rest = append(rest, p)
			}
		}
		d.pending = rest
	}
}

// visible returns the ids of the characters shown, in order.
func (d *Doc) visible() []ID {
	var out []ID
	for _, e := range d.elems {
		if !e.deleted {
			out = append(out, e.id)
		}
	}
	return out
}

// Text is what the phone shows.
func (d *Doc) Text() string {
	var b strings.Builder
	for _, e := range d.elems {
		if !e.deleted {
			b.WriteRune(e.ch)
		}
	}
	return b.String()
}

// Edit applies a local edit given as positions in the visible text: delete
// del characters starting at at, then type ins there. It returns the ops it
// made, for sending to the other phones.
func (d *Doc) Edit(at, del int, ins string) ([]Op, error) {
	vis := d.visible()
	if at < 0 || del < 0 || at+del > len(vis) {
		return nil, fmt.Errorf("edit out of range: at %d, delete %d, text has %d characters", at, del, len(vis))
	}
	var ops []Op
	for _, target := range vis[at : at+del] {
		d.clock++
		op := Op{ID: ID{C: d.clock, R: d.Phone}, Ref: target, Del: true}
		d.integrate(op)
		ops = append(ops, op)
	}
	ref := head
	if at > 0 {
		ref = vis[at-1]
	}
	for _, ch := range ins {
		d.clock++
		op := Op{ID: ID{C: d.clock, R: d.Phone}, Ref: ref, Ch: ch}
		d.integrate(op)
		ops = append(ops, op)
		ref = op.ID
	}
	return ops, nil
}

// SyncFrom gives d every op src has that d lacks, in src's order (which is
// causal: nothing comes before the character it refers to).
func (d *Doc) SyncFrom(src *Doc) {
	for _, op := range src.log {
		if !d.seen[op.ID] {
			d.Receive(op)
		}
	}
}

// ---- the page's history

// Event is one thing that happened on the page.
type Event struct {
	K    string `json:"k"` // edit | sync | online | offline
	R    int    `json:"r"` // phone (edit, online, offline)
	At   int    `json:"at,omitempty"`
	Del  int    `json:"del,omitempty"`
	Ins  string `json:"ins,omitempty"`
	From int    `json:"from,omitempty"`
	To   int    `json:"to,omitempty"`
}

// Params: the shared starting text and everything since.
type Params struct {
	Base   string  `json:"base"`
	Phones int     `json:"phones"`
	Events []Event `json:"events"`
	Demo   bool    `json:"demo"` // also return the example history
}

// Base is the note both phones start from.
const Base = "Teh quick brown fox jumsp over the lazy dog."

func Defaults() Params { return Params{Base: Base, Phones: 2} }

// Span is a stretch of text with one author, and, in the last-writer-wins view,
// what happened to it.
type Span struct {
	A int    `json:"a"`           // -1 base text, else the phone that typed it
	T string `json:"t"`           // the characters
	X string `json:"x,omitempty"` // "lost" (typed, gone) or "back" (deleted, returned)
}

// Phone is one phone's state after the history.
type Phone struct {
	Text    string `json:"text"`
	Runs    []Span `json:"runs"`
	Pending int    `json:"pending"` // its own changes some other phone hasn't received
	Online  bool   `json:"online"`
	Edits   int    `json:"edits"` // changes it has made (characters typed or deleted)
}

// Stats compare the two ways of merging.
type Stats struct {
	Mode        string  `json:"mode"`
	Label       string  `json:"label"`
	Text        string  `json:"text"`
	KeptTyped   float64 `json:"keptTyped"`   // typed characters nobody deleted that survive
	KeptDeletes float64 `json:"keptDeletes"` // deletions that stay deleted
	Lost        int     `json:"lost"`        // typed characters that vanished
	Back        int     `json:"back"`        // deleted characters that came back
	Agree       bool    `json:"agree"`       // every phone shows the same thing afterwards
}

// Result is what the page gets.
type Result struct {
	Phones []Phone `json:"phones"`
	Synced bool    `json:"synced"` // the phones show the same text right now
	Merged []Span  `json:"merged"` // everything merged by the CRDT
	LWW    []Span  `json:"lww"`    // last writer wins, marked up against it
	Winner int     `json:"winner"` // whose copy last-writer-wins keeps (-1: nobody edited)
	Stats  []Stats `json:"stats"`  // last writer wins, then the CRDT
	Demo   []Event `json:"demo,omitempty"`
	Base   string  `json:"base"`
}

// replay is a history played out.
type replay struct {
	docs   []*Doc
	last   []int         // event index of each phone's last edit, -1 if none
	saved  []map[ID]bool // what each phone showed right after its last edit
	online []bool
}

// Replay runs a history.
func Replay(p Params) (*replay, error) {
	if p.Phones < 2 || p.Phones > 3 {
		return nil, fmt.Errorf("phones must be 2 or 3")
	}
	if utf8.RuneCountInString(p.Base) > 2000 || len(p.Events) > 20000 {
		return nil, fmt.Errorf("history too long")
	}
	docs := make([]*Doc, p.Phones)
	for i := range docs {
		docs[i] = NewDoc(i, p.Base)
	}
	last := make([]int, p.Phones)
	saved := make([]map[ID]bool, p.Phones)
	online := make([]bool, p.Phones)
	for i := range last {
		last[i] = -1
		online[i] = true
	}
	ok := func(r int) bool { return r >= 0 && r < p.Phones }
	chars := 0
	for k, e := range p.Events {
		switch e.K {
		case "edit":
			if !ok(e.R) {
				return nil, fmt.Errorf("event %d: no phone %d", k, e.R)
			}
			chars += utf8.RuneCountInString(e.Ins) + e.Del
			if chars > 20000 {
				return nil, fmt.Errorf("history too long")
			}
			if _, err := docs[e.R].Edit(e.At, e.Del, e.Ins); err != nil {
				return nil, fmt.Errorf("event %d: %w", k, err)
			}
			last[e.R] = k
			saved[e.R] = map[ID]bool{}
			for _, id := range docs[e.R].visible() {
				saved[e.R][id] = true
			}
		case "sync":
			if !ok(e.From) || !ok(e.To) {
				return nil, fmt.Errorf("event %d: bad sync", k)
			}
			docs[e.To].SyncFrom(docs[e.From])
		case "online", "offline":
			if !ok(e.R) {
				return nil, fmt.Errorf("event %d: no phone %d", k, e.R)
			}
			online[e.R] = e.K == "online"
		default:
			return nil, fmt.Errorf("event %d: unknown kind %q", k, e.K)
		}
	}
	return &replay{docs: docs, last: last, saved: saved, online: online}, nil
}

// all is every op from every phone merged into one copy: what the CRDT gives
// once everyone has synced.
func all(p Params, docs []*Doc) *Doc {
	m := NewDoc(-1, p.Base)
	for _, d := range docs {
		m.SyncFrom(d)
	}
	return m
}

// runs groups consecutive characters by author and mark.
func runs(elems []elem, mark func(e elem) (show bool, x string)) []Span {
	var out []Span
	for _, e := range elems {
		show, x := mark(e)
		if !show {
			continue
		}
		a := e.id.R
		if n := len(out); n > 0 && out[n-1].A == a && out[n-1].X == x {
			out[n-1].T += string(e.ch)
			continue
		}
		out = append(out, Span{A: a, T: string(e.ch), X: x})
	}
	return out
}

func text(rs []Span, skip string) string {
	var b strings.Builder
	for _, r := range rs {
		if r.X != skip {
			b.WriteString(r.T)
		}
	}
	return b.String()
}

// Simulate replays the history and lays out both merges.
func Simulate(p Params) (Result, error) {
	rp, err := Replay(p)
	if err != nil {
		return Result{}, err
	}
	docs, last, online := rp.docs, rp.last, rp.online
	merged := all(p, docs)
	res := Result{Base: p.Base, Winner: -1, Synced: true}

	for i, d := range docs {
		ph := Phone{Text: d.Text(), Online: online[i]}
		ph.Runs = runs(d.elems, func(e elem) (bool, string) { return !e.deleted, "" })
		for _, op := range d.log {
			if op.ID.R != i {
				continue
			}
			ph.Edits++
			for j, o := range docs {
				if j != i && !o.seen[op.ID] {
					ph.Pending++
					break
				}
			}
		}
		if ph.Text != docs[0].Text() {
			res.Synced = false
		}
		res.Phones = append(res.Phones, ph)
	}

	// last writer wins: the copy saved most recently replaces the rest, as
	// it was when it was saved
	for i, k := range last {
		if k >= 0 && (res.Winner < 0 || k > last[res.Winner]) {
			res.Winner = i
		}
	}
	winner := map[ID]bool{} // characters on the winning copy
	if res.Winner >= 0 {
		winner = rp.saved[res.Winner]
	} else {
		for _, id := range docs[0].visible() {
			winner[id] = true
		}
	}

	res.Merged = runs(merged.elems, func(e elem) (bool, string) { return !e.deleted, "" })
	// every character either merge could show, marked by what LWW did to it
	res.LWW = runs(merged.elems, func(e elem) (bool, string) {
		switch {
		case !e.deleted && winner[e.id]:
			return true, ""
		case !e.deleted && !winner[e.id]:
			return true, "lost"
		case e.deleted && winner[e.id]:
			return true, "back"
		}
		return false, ""
	})

	// the numbers: typed characters nobody deleted, and deletions
	var typed, typedKeptLWW, deleted, deletedKeptLWW int
	for _, e := range merged.elems {
		isTyped := e.id.R >= 0
		if isTyped && !e.deleted {
			typed++
			if winner[e.id] {
				typedKeptLWW++
			}
		}
		if e.deleted {
			deleted++
			if !winner[e.id] {
				deletedKeptLWW++
			}
		}
	}
	frac := func(a, b int) float64 {
		if b == 0 {
			return 1
		}
		return float64(a) / float64(b)
	}
	lost, back := 0, 0
	for _, r := range res.LWW {
		switch r.X {
		case "lost":
			lost += utf8.RuneCountInString(r.T)
		case "back":
			back += utf8.RuneCountInString(r.T)
		}
	}
	// (base text can't be "lost": a base character missing from the winner
	// was deleted there, so it's deleted in the merge too)
	res.Stats = []Stats{
		{Mode: "lww", Label: "Last writer wins", Text: text(res.LWW, "lost"), KeptTyped: frac(typedKeptLWW, typed), KeptDeletes: frac(deletedKeptLWW, deleted), Lost: lost, Back: back, Agree: true},
		{Mode: "crdt", Label: "CRDT (RGA)", Text: merged.Text(), KeptTyped: 1, KeptDeletes: 1, Lost: 0, Back: 0, Agree: true},
	}
	return res, nil
}

// ---- the example

// Demo is the scripted example: both phones go offline; phone A fixes "Teh"
// and adds "sly " before "fox"; phone B fixes "jumsp" and adds "small "
// before "fox"; then both come back online and sync. Edits are split into
// keystrokes so the page can replay them as typing.
func Demo() []Event {
	var ev []Event
	text := []string{Base, Base}
	type edit struct {
		r        int
		old, new string // replace old (or insert before old, when new ends with old)
	}
	keystrokes := func(r, at, del int, ins string) {
		for i := 0; i < del; i++ {
			ev = append(ev, Event{K: "edit", R: r, At: at + del - 1 - i, Del: 1})
		}
		for i, ch := range []rune(ins) {
			ev = append(ev, Event{K: "edit", R: r, At: at + i, Ins: string(ch)})
		}
		rs := []rune(text[r])
		text[r] = string(rs[:at]) + ins + string(rs[at+del:])
	}
	at := func(r int, s string) int { return utf8.RuneCountInString(text[r][:strings.Index(text[r], s)]) }

	ev = append(ev, Event{K: "offline", R: 0}, Event{K: "offline", R: 1})
	// A: fix the first typo, then add a word before "fox"
	keystrokes(0, at(0, "Teh"), 3, "The")
	keystrokes(0, at(0, "fox"), 0, "sly ")
	// B: fix the other typo, then add a word at the same spot
	keystrokes(1, at(1, "jumsp"), 5, "jumps")
	keystrokes(1, at(1, "fox"), 0, "small ")
	ev = append(ev, Event{K: "online", R: 0}, Event{K: "online", R: 1},
		Event{K: "sync", From: 0, To: 1}, Event{K: "sync", From: 1, To: 0})
	return ev
}

// Run is the page's entry.
func Run(params json.RawMessage) (any, error) {
	p := Defaults()
	if err := registry.Decode(params, &p); err != nil {
		return nil, err
	}
	res, err := Simulate(p)
	if err != nil {
		return nil, err
	}
	if p.Demo {
		res.Demo = Demo()
	}
	return res, nil
}

// Report runs the example and prints both merges.
func Report() string {
	p := Defaults()
	p.Events = Demo()
	res, err := Simulate(p)
	if err != nil {
		return err.Error() + "\n"
	}
	var b strings.Builder
	fmt.Fprintf(&b, "start:    %s\nphone A:  fixes \"Teh\", adds \"sly \" before \"fox\" (offline)\nphone B:  fixes \"jumsp\", adds \"small \" before \"fox\" (offline)\n\n", Base)
	fmt.Fprintf(&b, "%-18s %-56s %7s %9s %5s %5s\n", "merge", "result", "typed", "deletes", "lost", "back")
	for _, s := range res.Stats {
		fmt.Fprintf(&b, "%-18s %-56q %6.0f%% %8.0f%% %5d %5d\n", s.Label, s.Text, s.KeptTyped*100, s.KeptDeletes*100, s.Lost, s.Back)
	}
	return b.String()
}

func init() {
	registry.Register(registry.Sim{Name: "local-first", Title: "Local-first sync", Run: Run, Report: Report})
}
