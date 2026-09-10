#!/bin/zsh
# E-005 sweep, NDIF only.
#
# Sequential so runs cannot collide on a cache. Each model is attempted several
# times: src/remote.py retries individual transport failures, but NDIF can also
# stall long enough to exhaust those, and every completed item is already cached,
# so a fresh attempt resumes rather than restarts.
set -u
cd "$(dirname "$0")/../../.."
MODELS=(
  "EleutherAI/gpt-j-6b"
  "meta-llama/Llama-3.1-8B"
  "meta-llama/Llama-3.1-70B"
  "meta-llama/Llama-3.1-405B"
)
for m in $MODELS; do
  echo "=== $m ==="
  for attempt in 1 2 3; do
    .venv/bin/python agents/engineer/workspace/possession_lift.py --model "$m" 2>&1 \
      | grep -viE "downloading|received|queued|dispatched|✓|⠋|⠙|⠹|⠸|⠼|⠴|⠦|tokenization" \
      | grep -v "^$"
    cache="agents/engineer/workspace/lift/${m//\//_}.json"
    n=$(.venv/bin/python -c "import json;print(len(json.load(open('$cache'))))" 2>/dev/null || echo 0)
    if [[ "$n" -ge 165 ]]; then break; fi
    echo "-- $m incomplete ($n/165), attempt $attempt failed; retrying"
    sleep 20
  done
done
echo "ALL MODELS DONE"
