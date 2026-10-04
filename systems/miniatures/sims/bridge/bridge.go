//go:build js && wasm

// Package bridge exposes the registered miniatures to the browser as
// miniRun(name, paramsJSON) -> resultJSON, then fires a "mini-ready" event.
package bridge

import (
	"encoding/json"
	"errors"
	"syscall/js"

	"miniatures/sims/registry"
)

// Serve installs miniRun and blocks forever.
func Serve() {
	js.Global().Set("miniRun", js.FuncOf(func(this js.Value, args []js.Value) any {
		fail := func(err error) any {
			b, _ := json.Marshal(map[string]string{"error": err.Error()})
			return string(b)
		}
		if len(args) < 1 {
			return fail(errors.New("miniRun(name, paramsJSON)"))
		}
		sim, err := registry.Get(args[0].String())
		if err != nil {
			return fail(err)
		}
		var params json.RawMessage
		if len(args) > 1 && args[1].Type() == js.TypeString {
			params = json.RawMessage(args[1].String())
		}
		out, err := sim.Run(params)
		if err != nil {
			return fail(err)
		}
		b, err := json.Marshal(out)
		if err != nil {
			return fail(err)
		}
		return string(b)
	}))
	js.Global().Call("dispatchEvent", js.Global().Get("Event").New("mini-ready"))
	select {}
}
