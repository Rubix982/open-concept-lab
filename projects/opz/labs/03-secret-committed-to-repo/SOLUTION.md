# Lab 03 · Solution (spoilers)

## Why the follow-up commit didn't help

Git keeps every version of every file. A new commit records the change and
leaves the old snapshot exactly as it was: `git show HEAD~2:storage.py` (the "Add S3 upload" commit) still
prints the keys. This is Lab 01's lesson again: image layers and git commits are
both append-only.

## Step 0, always: rotate

Deactivate the key in AWS and issue a new one **before** cleaning git. Once a key
has been public for even a minute, assume it's copied: scrapers, forks, clones,
CI caches. Scrubbing history stops future readers. Only rotation stops someone
who already has it. In a real incident you'd also check CloudTrail for what the
key was used for.

## Scrub

`replacements.txt` (outside the repo):
```
regex:AKIA[A-Z2-7]{16}==>REMOVED
regex:aws_secret_access_key="[^"]*"==>aws_secret_access_key="REMOVED"
```

```bash
cd repo
git filter-repo --replace-text ../replacements.txt --force
```

`--force` is needed because this isn't a fresh clone. filter-repo rewrites every
commit, then expires the reflog and garbage-collects, so the old objects are really
gone. With older tools (`git filter-branch`, interactive rebase) you must do that yourself:
```bash
git reflog expire --expire=now --all && git gc --prune=now
```
Skip it and `check.sh` catches you: the old commits are unreachable but still in `.git`.

Notice the hashes: every commit from "Add S3 upload" onward has a **new** hash.
On a shared repo that means `git push --force`, everyone else must re-clone (or
hard-reset), and any open PR or fork still carries the old commits. GitHub may
also keep cached views of old commits until you ask their support to purge them.

## Prevent

`.git/hooks/pre-commit`:
```sh
#!/bin/sh
exec gitleaks git --pre-commit --staged --no-banner
```
```bash
chmod +x .git/hooks/pre-commit
```

## What the hook can't catch

- **Hooks aren't cloned.** `.git/hooks` is local. Each developer has to install it
  (or use the `pre-commit` framework or `core.hooksPath` with a committed hooks folder).
- **It can be skipped** with `git commit --no-verify`. So also run gitleaks in CI and
  turn on GitHub secret scanning / push protection, which run on the server where
  nobody can skip them.
- **Pattern-based.** It catches key formats it knows (AWS, GitHub, Stripe…) and
  high-entropy strings, but not a plain password like `hunter2`.
