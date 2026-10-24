# Lab 06 · Replay Attack via Insecure Webhooks

**Time:** ~40 min · **Needs:** Python 3 (standard library only) · **Cost:** free, all local

## The incident

The shop takes payments through a provider called Paylark. When a payment goes
through, Paylark POSTs a `payment.succeeded` event to the shop's `/webhook`, and
the shop ships the order.

Finance noticed three orders shipped that were never paid, and one paid order
that shipped three times. Nobody hacked Paylark. Someone has been talking to the
shop's webhook directly.

## Setup

```bash
python3 app/server.py               # terminal 1: the shop, on 127.0.0.1:8086
curl -s localhost:8086/orders       # terminal 2: what the shop thinks happened
```

`tools/send.py` plays both Paylark and the attacker:

```bash
python3 tools/send.py fresh  ord_1001   # Paylark: a real, signed event
python3 tools/send.py forge  ord_1002   # attacker: no secret, invented signature
python3 tools/send.py tamper ord_1003   # attacker: a real signature, body edited afterwards
python3 tools/send.py stale  ord_1002   # attacker: a real event captured 10 minutes ago
python3 tools/send.py replay            # attacker: resend the last real event, byte for byte
```

Restart the shop to reset the orders.

## Your job

1. **Break it first.** Run each attack and watch `/orders`. Which attacks work?
   Write down why each one works before you change anything.
2. **Fix `app/server.py`** so that only real, fresh, first-time events ship an order.
   Hints, one at a time if you're stuck:
   - Read `sign()` in `tools/send.py`. That's Paylark's side of the contract.
     Your side has to recompute the same thing and compare.
   - Sign over the **raw bytes** you received, not `json.dumps(json.loads(raw))`.
     Re-serialising changes spacing and key order, and the signature stops matching.
   - Comparing two strings with `==` stops at the first different character, so how
     long it takes leaks how much of the guess was right. Look in the `hmac` module.
   - A valid signature proves Paylark sent it, **not** that it was sent just now.
     What in the header lets you reject old messages?
   - A replay sent within that window still has a valid signature and a fresh
     timestamp. What in the body is unique per event?
3. **Prove it.** `./check.sh` starts its own copy of the shop on port 18086, runs
   every attack and one honest event, and passes only when all attacks fail and
   the honest one ships exactly once.
4. **Write the retro** (below).

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why "the header is present" checks nothing:
- What the signature proves, and what it doesn't:
- Why the timestamp is inside the signed message, not just next to it:
- Why replays need an event-ID store even with a timestamp check:
- What should a duplicate get back, 200 or 4xx? (think about Paylark's retries):
