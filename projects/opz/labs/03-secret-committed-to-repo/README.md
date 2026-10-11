# Lab 03 · Secret Committed to a Repo

**Time:** ~30–40 min · **Needs:** git, `gitleaks`, `git-filter-repo` (`brew install gitleaks git-filter-repo`) · **Cost:** free, all local

## The incident

A teammate hardcoded AWS keys in `storage.py`, committed, noticed eleven minutes
later, and pushed a follow-up commit: *"Oops, remove hardcoded keys"*. The
current code looks clean, and code review of the latest version would pass.

But the repo is public, and bots scrape new commits on GitHub for keys within minutes.

## Setup

```bash
./setup.sh        # builds ./repo with a fresh fake key; re-run any time to start over
cd repo
```

## Your job

1. **See the leak yourself.** Prove the key is still in the repo even though
   no current file contains it. Find it at least two ways.
   Hints, one at a time if you're stuck:
   - `git log -p`. What does the "Oops" commit's diff show?
   - `git show <hash-of-the-commit-before-Oops>:storage.py`
   - `gitleaks git -v .`
2. **Rotate first (on paper).** In real life, before touching git, what do you do
   with the key, and why must it happen first? Answer this in the retro.
3. **Scrub the history.** Remove both values (the access key and the secret key)
   from **every** commit. Keep the rest of the history; deleting `.git` and
   starting over doesn't count.
   Look up: `git filter-repo --replace-text`. Then ask yourself: after rewriting,
   are the old commits really gone from `.git`? (Look up `git reflog`.)
4. **Stop the next one.** Add a pre-commit hook that runs gitleaks on staged
   changes, so a new key can't be committed. Look up: `gitleaks git --pre-commit --staged`.
5. **Prove it.** Run `../check.sh` until it says `LAB PASSED`.
6. **Write the retro** (below).

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why "Oops, remove hardcoded keys" didn't remove them: Every commit is a full snapshot and a new commit never changes old ones, so "Add S3 upload" still holds the old storage.py with the keys. Append-only, like Docker layers in Lab 01.
- Why rotating the key comes before scrubbing history: Once public, assume the key is already copied. Rewriting history can't reach those copies, but rotating makes every copy worthless. Rotate always; rewrite only when the leak can't be rotated (personal data, hostnames) or to stop scanners re-flagging a dead key.
- What rewriting history breaks for everyone else who has the repo: Every commit hash from the leak onward changes, so it needs a `git push --force`. Everyone else must re-clone (or fetch + `git reset --hard origin/main`) and re-apply unpushed work; forks and open PRs keep the old commits, key included.
- The fix (scrub + prevent): Rotate → scrub → prevent. Rotate the key first; scrub every commit with `git filter-repo --replace-text` (which also expires the reflog and garbage-collects); prevent with a gitleaks pre-commit hook, backed by gitleaks in CI and GitHub push protection.
- What the pre-commit hook can't catch: Secrets with no recognisable pattern (a plain password); anyone who never installed it (hooks aren't cloned); anyone who skips it with `git commit --no-verify`. That's why the server-side checks matter.
