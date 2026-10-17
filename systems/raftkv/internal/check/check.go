package check

import (
	"errors"
	"sort"
)

// Verdict is one key's result: operations on different keys never constrain
// each other, so each key's history is checked on its own.
type Verdict struct {
	Key string
	Ops int
	OK  bool
	Why string
}

// ErrNoChecker fails closed until the checker is chosen (see review-queue.md).
var ErrNoChecker = errors.New("check: no linearizability checker yet; awaiting the person's choice (porcupine, or one written here)")

// ByKey checks each key's history.
func ByKey(history []Op) ([]Verdict, error) {
	byKey := map[string][]Op{}
	for _, op := range history {
		byKey[op.Key] = append(byKey[op.Key], op)
	}
	keys := make([]string, 0, len(byKey))
	for k := range byKey {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	return nil, ErrNoChecker
}
