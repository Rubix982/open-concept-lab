#!/usr/bin/env bash
# Makes the lab's virtualenv and installs PyJWT into it, in case you want it for
# the fix. The broken app itself needs only the standard library.
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "Ready. source .venv/bin/activate, then: python app/server.py"
