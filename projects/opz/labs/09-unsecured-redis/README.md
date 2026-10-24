# Lab 09 · Unsecured Redis Allows Remote Access

**Time:** ~40 min · **Needs:** Docker Compose · **Cost:** free, all local

## The incident

A security scanner flagged port 6309 on a dev server. Somebody then found that the
session tokens of logged-in users could be read straight out of Redis, from
another machine, with no password. Internet-wide scanners find open Redis within
minutes, and a common next step is `CONFIG SET dir` + `SAVE` to write a file
(an SSH key, a cron job) onto the server.

## Setup

```bash
./setup.sh                        # app on localhost:8009, Redis behind it
curl -s localhost:8009/login      # makes a session token, stored in Redis
tools/attacker.sh                 # someone else on the network: KEYS *
tools/attacker.sh GET 'session:<paste a token>'
tools/attacker.sh CONFIG GET dir  # they could write files here
```

`tools/attacker.sh` runs `redis-cli` in a throwaway container that is **not** on
the app's network and connects through your machine's published port, the way
another machine on your network would.

## Your job

1. **Map the exposure.** Who can reach Redis, and what can they do once
   connected? Hints, one at a time if you're stuck:
   - Read `ports:` in `compose.yaml`. Which service actually needs to talk to Redis,
     and does it go through the host port?
   - `docker port opz-lab09-redis` and `docker network inspect opz-lab09_default`.
   - Redis has a "protected mode" that should refuse remote clients without a
     password. Why didn't it help here? (Read the comment in compose.yaml.)
2. **Fix it, in layers.** Each layer should hold even if another one fails:
   - **Network:** Redis reachable only by the app.
   - **Authentication:** no anonymous clients, even on the app's network. Look up
     Redis ACLs (`--aclfile`, `user default off`). The app already supports
     `REDIS_USERNAME` and `REDIS_PASSWORD_FILE` (lab 02's secrets lesson).
   - **Least privilege:** the app's user shouldn't be able to run `CONFIG`,
     `FLUSHALL`, `DEBUG`… Look at ACL categories, `-@dangerous` in particular.
   - Bonus: store a hash of the password in the ACL file, not the password itself.
3. **Prove it.** `./setup.sh`, then `./check.sh`. It tests from outside the network,
   from inside it without a password, and that the app still works.
4. **Write the retro** (below). **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Who could reach Redis before, and how:
- Why protected mode didn't save us:
- The three layers I added, and what each one stops on its own:
- What `-@dangerous` blocks, and why the app never needed it:
- What still isn't covered (hint: the traffic itself):
