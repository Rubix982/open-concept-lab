// Package registry is where every miniature signs in, so the command line
// and the browser build can run any of them by name.
package registry

import (
	"encoding/json"
	"fmt"
	"sort"
)

// Sim is one miniature.
type Sim struct {
	Name  string
	Title string
	// Run takes the page's parameters as JSON (missing fields keep their
	// defaults) and returns something json.Marshal can encode: the trace the
	// page replays plus the numbers it reports.
	Run func(params json.RawMessage) (any, error)
	// Report runs the broken and fixed versions side by side and returns a
	// short plain-text table for the terminal.
	Report func() string
}

var sims = map[string]Sim{}

// Register adds a miniature; call it from the package's init.
func Register(s Sim) {
	if _, dup := sims[s.Name]; dup {
		panic("registry: duplicate sim " + s.Name)
	}
	sims[s.Name] = s
}

// Get looks a miniature up by name.
func Get(name string) (Sim, error) {
	s, ok := sims[name]
	if !ok {
		return Sim{}, fmt.Errorf("no sim called %q (have %v)", name, Names())
	}
	return s, nil
}

// Names lists the registered miniatures, sorted.
func Names() []string {
	out := make([]string, 0, len(sims))
	for n := range sims {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// Decode fills p from the JSON params, leaving fields that are absent at the
// defaults p already holds.
func Decode(params json.RawMessage, p any) error {
	if len(params) == 0 || string(params) == "null" {
		return nil
	}
	return json.Unmarshal(params, p)
}
