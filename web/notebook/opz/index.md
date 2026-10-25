---
title: opz
sidebar_label: opz
sidebar_position: 1
description: Deployment and security, learned one small broken system at a time.
---

# opz

<Status kind="draft">Practice log, growing one lab at a time</Status>

I had been putting off learning deployment until it showed up inside a big
project. That's backwards: a big project hides each lesson under everything
else going on. So this is the opposite approach. Each lab shrinks one real
incident to something that runs on a laptop in under an hour, and nothing in it
depends on anything else.

Every lab follows the same five steps:

```
break → diagnose → fix → prove → retro
```

The proof is a `check.sh` that passes only when the problem is actually gone,
not when it's hidden. The retro is five lines, and it's the part that sticks.

## Where it stands

<Claim
  label="Progress"
  record={{
    Labs: "4 solved",
    Checklist: "4 of 244 lines ticked",
    Next: "Kubernetes resource limits, or webhook replay attacks",
  }}
>
  Four labs in: three on secrets, one on Kubernetes debugging. The first three
  taught one lesson three ways.
</Claim>

The full list lives under [Labs](/labs): every scenario from my original notes,
grouped into four tracks.
- **A, DevOps & security:** local labs.
- **B, distributed systems:** built from scratch.
- **C, AI systems & security:** serving small models, attacks on them, detecting trouble.
- **D, cloud:** labs that need a real account.

## The labs

### 01 · Hardcoded credentials in a Dockerfile

A token baked into the image with `ENV`, plus a `.env` file "cleaned up" with
`rm` in a later step. Both leaked. `ENV` is image metadata that anyone who can
pull the image can read. And image layers are append-only: `rm` adds a new layer
that hides the file, while the old layer still holds it. Fix: `.dockerignore`,
and supply the token when the container starts.
[Lab →](https://github.com/Rubix982/opz/tree/main/labs/01-hardcoded-creds-dockerfile)

### 02 · Secrets in environment variables

With the image clean, the token still showed up in `docker inspect`, in every
child process, and in `docker compose config`. Environment variables are
*pushed*: copied everywhere by default. A file is *pulled*: only code that opens
it gets the secret. Fix: Compose secrets, with the app reading
`/run/secrets/api_token`. What it doesn't fix: anyone with `docker exec` can
still read the file. It stops accidental leaks, not a deliberate insider.
[Lab →](https://github.com/Rubix982/opz/tree/main/labs/02-env-var-secret-exposure)

### 03 · A secret committed to a repo

"Oops, remove hardcoded keys" removed nothing. Git keeps every snapshot, so the
key sat in the commit before. Scrubbing it with `git filter-repo` changes every
commit hash after the leak, and anyone who already cloned the repo still has the
key. The order is **rotate → scrub → prevent**. Rotation is the only step that
reaches copies you can't see. A gitleaks pre-commit hook catches the next one,
but hooks aren't cloned and can be skipped, so the real backstop runs on the server.
[Lab →](https://github.com/Rubix982/opz/tree/main/labs/03-secret-committed-to-repo)

### 04 · Debugging a CrashLoopBackOff pod

Two layered bugs on a local kind cluster. The logs showed the first: a bad
`APP_MODE` in a ConfigMap. That was a setting, not a code bug, so it needed no
new image. With that fixed the app logged a clean start and kept dying anyway.
Only `kubectl describe` showed why: the liveness probe was asking for the wrong
path and killing a healthy container. Logs are what the app said; events are what
Kubernetes did.
[Lab →](https://github.com/Rubix982/opz/tree/main/labs/04-crashloopbackoff)

## What I've noticed so far

Labs 01 and 03 are the same lesson in two systems. Image layers and git commits
are both append-only, so a later delete only hides what came before. Once I saw
that, lab 03 was half-solved before I started.

<Aside>
  On labs 01–03 I asked for the fix and learned it from the retro. On lab 04 I
  diagnosed both bugs myself from hints. That one I remember best.
</Aside>

The retro questions that taught the most were the ones about what a fix
*doesn't* cover: what `docker exec` can still read, what a pre-commit hook can't
catch. A fix stated without its limits is the kind of claim I'd distrust in a paper.

Lab 04 also produced a small incident playbook: roll back if an earlier version
worked; capture logs and events before anything deletes the pods; scale to zero
only if each restart does real damage; then diagnose.
