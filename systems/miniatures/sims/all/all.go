// Package all imports every miniature so each registers itself.
package all

import (
	_ "miniatures/sims/batching"
	_ "miniatures/sims/cacherouter"
	_ "miniatures/sims/disagg"
	_ "miniatures/sims/doublecharge"
	_ "miniatures/sims/herd"
	_ "miniatures/sims/localfirst"
	_ "miniatures/sims/straggler"
)
