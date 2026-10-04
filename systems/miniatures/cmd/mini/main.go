// The terminal runner.
//
//	go run ./cmd/mini                 list the miniatures
//	go run ./cmd/mini cache-router    broken vs fixed, side by side
//	go run ./cmd/mini cache-router '{"policy":"cache"}' > out.json
package main

import (
	"encoding/json"
	"fmt"
	"os"

	_ "miniatures/sims/all"
	"miniatures/sims/registry"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("miniatures:")
		for _, n := range registry.Names() {
			s, _ := registry.Get(n)
			fmt.Printf("  %-18s %s\n", n, s.Title)
		}
		return
	}
	sim, err := registry.Get(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if len(os.Args) == 2 {
		fmt.Print(sim.Report())
		return
	}
	out, err := sim.Run(json.RawMessage(os.Args[2]))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	json.NewEncoder(os.Stdout).Encode(out)
}
