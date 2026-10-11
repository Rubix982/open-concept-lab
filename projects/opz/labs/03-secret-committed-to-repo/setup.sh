#!/usr/bin/env bash
# Builds ./repo: a small project whose history contains a committed AWS-style
# key that was later "removed". Re-run any time to start the lab over.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf repo .lab-token

# A fresh fake key each run, assembled here so this lab's own files never contain one.
rand() { LC_ALL=C tr -dc "$1" </dev/urandom | head -c "$2" || true; }
key="AKIA$(rand 'A-Z2-7' 16)"
secret="$(rand 'A-Za-z0-9' 40)"
printf '%s\n' "$key" > .lab-token

git init -q -b main repo && cd repo
git config user.name "Dev Teammate"; git config user.email "dev@example.com"
c() { git add -A && GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }

cat > app.py <<'PY'
from storage import upload

if __name__ == "__main__":
    upload("report.csv")
PY
cat > README.md <<'MD'
# report-uploader
Uploads the nightly report to S3.
MD
c "2026-09-01T10:00:00" "Initial uploader"

cat > storage.py <<PY
import boto3

s3 = boto3.client(
    "s3",
    aws_access_key_id="$key",
    aws_secret_access_key="$secret",
)


def upload(path: str) -> None:
    s3.upload_file(path, "nightly-reports", path)
PY
c "2026-09-02T14:30:00" "Add S3 upload"

cat > storage.py <<'PY'
import boto3

# Credentials come from the environment (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY).
s3 = boto3.client("s3")


def upload(path: str) -> None:
    s3.upload_file(path, "nightly-reports", path)
PY
c "2026-09-02T14:41:00" "Oops, remove hardcoded keys"

printf '\n## Running\nSet AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, then `python app.py`.\n' >> README.md
c "2026-09-05T09:15:00" "Document how to run"

echo "repo/ ready: 4 commits. The key looks gone from the current files. Is it?"
