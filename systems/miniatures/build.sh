#!/bin/sh
# Test every miniature, then compile them all into site/mini.wasm for the pages.
set -e
cd "$(dirname "$0")"
go vet ./...
go test ./...
GOOS=js GOARCH=wasm go build -trimpath -ldflags="-s -w" -o site/mini.wasm ./cmd/wasm
cp "$(go env GOROOT)/lib/wasm/wasm_exec.js" site/
ls -lh site/mini.wasm | awk '{print "site/mini.wasm", $5}'
# Save the runs each page shows by default, so pages also work opened from disk.
node bake.mjs
