package kv

import (
	"bytes"
	"encoding/gob"
	"testing"
)

func mustEncode(t *testing.T, op Op) []byte {
	t.Helper()
	var buf bytes.Buffer
	if err := gob.NewEncoder(&buf).Encode(op); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}
