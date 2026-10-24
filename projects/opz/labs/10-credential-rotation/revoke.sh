#!/usr/bin/env bash
# Step 2 of the runbook: revoke every password except the current one.
# Run only once every service has switched to the new password.
set -euo pipefail
cd "$(dirname "$0")"
SECRETS_DIR=${SECRETS_DIR:-./secrets}
current=$(tr -d '[:space:]' < "$SECRETS_DIR/db_password.txt")
# In place again: a bind-mounted single file must keep its inode.
echo "$current" > "$SECRETS_DIR/db_valid_passwords.txt"
echo "revoked: the db now accepts only ...${current: -6}"
