// Package check decides whether a recorded history of key-value operations is
// linearizable: whether some order of the operations, each placed between its
// call and its return, explains every value every read saw.
package check

// Op is one client operation as recorded: when it was called, when it
// returned, and what it saw. An operation whose client gave up has Unknown set:
// it may have taken effect at any time after its call, or never.
type Op struct {
	Client  int    `json:"client"`
	Kind    string `json:"kind"` // "get" or "put"
	Key     string `json:"key"`
	Value   string `json:"value"` // what a put wrote, or what a get read
	Call    int64  `json:"call"`  // nanoseconds, one clock for the whole run
	Return  int64  `json:"return"`
	Unknown bool   `json:"unknown,omitempty"`
}
