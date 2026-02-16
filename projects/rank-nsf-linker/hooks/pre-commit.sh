#!/bin/bash

# Pre-commit hook for Go projects
# Runs fast checks before allowing commit

set -e

echo "🔍 Running pre-commit checks..."

# Only check staged Go files
STAGED_GO_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.go$' || true)

if [ -z "$STAGED_GO_FILES" ]; then
    echo "✓ No Go files to check"
    exit 0
fi

echo "📝 Checking ${STAGED_GO_FILES}"

# Format check
echo "→ Running gofmt..."
UNFORMATTED=$(gofmt -l $STAGED_GO_FILES)
if [ -n "$UNFORMATTED" ]; then
    echo "❌ Files need formatting:"
    echo "$UNFORMATTED"
    echo ""
    echo "Run: make fmt"
    exit 1
fi

# Imports check
echo "→ Running goimports..."
if command -v goimports &> /dev/null; then
    for FILE in $STAGED_GO_FILES; do
        goimports -w "$FILE"
    done
    git add $STAGED_GO_FILES
fi

# Quick vet
echo "→ Running go vet..."
go vet ./...

# Fast lint (only changed files)
echo "→ Running golangci-lint (fast)..."
golangci-lint run --new-from-rev=HEAD --timeout=3m $STAGED_GO_FILES

echo "✅ All checks passed!"
exit 0
