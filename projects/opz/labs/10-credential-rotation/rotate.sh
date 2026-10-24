#!/usr/bin/env bash
# The rotation runbook, as a script. Step 1 of 2: introduce the new password.
#   1. the DBA adds a NEW password to the db (old and new both work now)
#   2. the new password is written to the services' secret file
# Revoking the old password is a separate, later step: ./revoke.sh
#
# Env: SECRETS_DIR (default ./secrets), COMPOSE_PROJECT_NAME (default opz-lab10).
set -euo pipefail
cd "$(dirname "$0")"
SECRETS_DIR=${SECRETS_DIR:-./secrets}
export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-opz-lab10}

new="pw_FAKE_lab10_$(date +%s)_$RANDOM"
echo "$new" >> "$SECRETS_DIR/db_valid_passwords.txt"
# Overwrite in place (same file, new contents). See SOLUTION.md for why "in place" matters.
cat > "$SECRETS_DIR/db_password.txt" <<<"$new"
echo "rotated: services' secret file now holds ...${new: -6}"
