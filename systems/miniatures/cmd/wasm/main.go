//go:build js && wasm

// The browser build of every miniature: site/mini.wasm. Build with ./build.sh.
package main

import (
	"miniatures/sims/bridge"
	_ "miniatures/sims/all"
)

func main() { bridge.Serve() }
