# Lab 17 · Log Injection Attack on Centralized Logging

**Time:** ~40 min · **Needs:** Python 3 (standard library only) · **Cost:** free, all local

The checklist names Fluent Bit. This lab uses a small Python shipper instead
(`pipeline/ship.py`), which reads the log one line at a time and turns each line
into one event, like Fluent Bit with no multiline rule. The attack and the fix
are the same either way, and there's nothing to install.

## The incident

During an investigation the security team found this in the central log store:

```
03:12:44  INFO  login succeeded user=admin ip=10.0.0.5
```

Nobody logged in as admin at 03:12. There's no session, and 10.0.0.5 isn't a
machine anyone recognises. The team spent a day treating it as a breach of the
admin account. It wasn't one. A user who signed up a minute earlier picked a
very strange username.

## Setup

```bash
python3 app/server.py                # terminal 1: accounts service on 127.0.0.1:8017, logs to logs/app.log
python3 tools/attack.py honest       # terminal 2: a normal signup + login
python3 tools/attack.py forge        # a username carrying a fake log line
python3 tools/attack.py hide         # a username carrying terminal control codes
python3 pipeline/ship.py             # ship logs/app.log -> logs/central.jsonl
python3 pipeline/view.py             # what on-call sees (try: python3 pipeline/view.py login)
```

Look at all three: `logs/app.log`, `logs/central.jsonl`, and the viewer's output
in a real terminal. Delete `logs/` to start clean.

## Your job

1. **Break it first.** After `forge` and `hide`, how many events does the store
   hold, and which ones are lies? Where did the `dave` line's text go in the viewer?
2. **Fix it.** You'll change `app/server.py` and `pipeline/view.py`. Leave
   `pipeline/ship.py` alone: it already understands JSON lines. Hints, one at a time:
   - The shipper's rule is "one line = one event". So who decides where a line
     ends, the app or the user?
   - Removing newlines from usernames *hides* the symptom but changes the
     evidence: investigators then see a username that was never submitted.
     The goal is the exact username, kept intact, inside one event.
   - Look at what `json.dumps("a\nb")` returns. How many lines is that?
   - `logging` lets you attach fields to a record with `extra={...}`, and a
     custom `Formatter` decides how a record is written.
   - The viewer is a terminal, and terminals obey escape codes in whatever they
     print. Give `show()` a way to print a value so control characters are visible
     instead of being followed.
3. **Prove it.** `./check.sh` runs its own copy on port 18017 with a temporary
   log folder, sends one honest user and both attacks, ships, and checks the
   store and the viewer.
4. **Write the retro** (below).

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why the forged line became a "real" event:
- Why stripping newlines isn't the fix:
- What structured logging changes, in one sentence:
- Why the log viewer is also part of the attack surface:
- What a forged event costs a team even when nothing was breached:
