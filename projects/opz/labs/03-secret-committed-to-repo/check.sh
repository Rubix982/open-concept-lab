#!/usr/bin/env bash
# Passes only when the key is gone from every corner of ./repo (not just the
# latest commit), the project's history is otherwise intact, and a pre-commit
# hook stops the next key from being committed.
set -u   # no pipefail: grep -q closing a pipe early must not count as "not found"
cd "$(dirname "$0")"
[ -d repo/.git ] && [ -f .lab-token ] || { echo "run ./setup.sh first"; exit 1; }
KEY="$(cat .lab-token)"
fail=0
cd repo

if grep -rqF "$KEY" . --exclude-dir=.git; then
  echo "FAIL  key in the current files"; fail=1
else echo "pass  current files clean"; fi

if git log --all -p | grep -qF "$KEY"; then
  echo "FAIL  key still in the commit history (git log --all -p)"; fail=1
else echo "pass  commit history clean"; fi

if git cat-file --batch-all-objects --batch 2>/dev/null | grep -aqF "$KEY"; then
  echo "FAIL  key still stored in .git (old commits kept alive by the reflog, or not yet garbage-collected)"; fail=1
else echo "pass  no object in .git holds the key"; fi

if gitleaks git . --no-banner >/dev/null 2>&1; then echo "pass  gitleaks finds nothing in history"
else echo "FAIL  gitleaks still reports leaks (run: gitleaks git -v ./repo)"; fail=1; fi

if git log --format=%s | grep -qx "Add S3 upload" && git log --format=%s | grep -qx "Document how to run" \
   && grep -q "## Running" README.md; then echo "pass  project history intact"
else echo "FAIL  history was lost (rewrite it, don't delete it)"; fail=1; fi

# Try to commit a brand-new key; a working pre-commit hook must refuse it.
probe="probe_$$.py"
before="$(git rev-parse HEAD)"
printf 'KEY = "AKIA%s"\n' "$(LC_ALL=C tr -dc 'A-Z2-7' </dev/urandom | head -c 16 || true)" > "$probe"
git add "$probe"
git -c user.name=check -c user.email=check@example.com commit -q -m "probe" >/dev/null 2>&1
if [ "$(git rev-parse HEAD)" != "$before" ]; then
  git reset -q --soft "$before"; echo "FAIL  a new key was committed: no pre-commit hook stopped it"; fail=1
else echo "pass  pre-commit hook blocked a new key"; fi
git reset -q -- "$probe"; rm -f "$probe"

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
