package scraperworker

import (
	ort "github.com/yalue/onnxruntime_go"
)

func probe() {
	// Attempt to call with what we used for AdvancedSession
	// This will error and tell us the correct signature if wrong
	ort.NewDynamicAdvancedSession("model.onnx", []string{"in"}, []string{"out"}, nil)
}
