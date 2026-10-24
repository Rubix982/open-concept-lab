#!/bin/sh
# Applies migrations/NNN_*.up.sql in order, skipping ones already recorded in
# schema_migrations. Each file and its record go in one transaction.
# Optional argument: stop after this version (e.g. "001").
set -eu
target="${1:-999}"
psql -q -v ON_ERROR_STOP=1 -c "CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
for f in /migrations/*.up.sql; do
  v=$(basename "$f" | cut -d_ -f1)
  [ "$v" \> "$target" ] && break
  if [ -n "$(psql -tA -c "SELECT 1 FROM schema_migrations WHERE version = '$v'")" ]; then continue; fi
  echo "migrate: applying $(basename "$f")"
  psql -q -v ON_ERROR_STOP=1 -1 -f "$f" -c "INSERT INTO schema_migrations (version) VALUES ('$v')"
done
echo "migrate: at $(psql -tA -c 'SELECT max(version) FROM schema_migrations')"
