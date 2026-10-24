# Lab 06 · Solution (spoilers)

## Why every attack worked

The shop only checked that a `Paylark-Signature` header **existed**. Anyone can
add a header. So:

| Attack | What it exploits |
|---|---|
| forge | No signature check at all |
| tamper | Same: the body isn't tied to the signature |
| stale | No check on when the message was signed |
| replay | No memory of which events were already handled |

## The fix

Four parts, in this order:

1. **Recompute the HMAC** over `"<t>." + raw body` with the shared secret.
   Use the raw bytes. Parsing and re-serialising the JSON changes bytes and breaks
   honest messages.
2. **Compare with `hmac.compare_digest`**, which takes the same time no matter
   where the strings differ. `==` returns sooner when the first characters are
   wrong, so an attacker measuring response times can guess a signature one
   character at a time.
3. **Reject old timestamps** (5 minutes is the usual window). This works only
   because `t` is *inside* the signed string. If it weren't, an attacker would just
   change it.
4. **Remember event IDs** and skip ones already handled. A replay sent 30 seconds
   later passes steps 1–3, so only this step stops it.

```python
TOLERANCE_S = 300
seen_events: set[str] = set()


def verify(raw: bytes, header: str) -> bool:
    try:
        parts = dict(item.split("=", 1) for item in header.split(","))
        ts, given = int(parts["t"]), parts["v1"]
    except (KeyError, ValueError):
        return False
    if abs(time.time() - ts) > TOLERANCE_S:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, given)
```

In `do_POST`:

```python
        if not verify(raw, self.headers.get("Paylark-Signature", "")):
            self._send(400, {"error": "bad signature"})
            return
        ...
        if event["id"] in seen_events:
            self._send(200, {"received": True, "duplicate": True})
            return
        seen_events.add(event["id"])
        handle_event(event)
```

## Details worth knowing

- **Duplicates get a 200, not an error.** Real providers retry when they don't get
  a 2xx (a timeout, say), so the same honest event really does arrive twice. A 4xx
  makes them keep retrying. "Already got it" is a success.
- **The ID store only has to cover the tolerance window.** Anything older is
  rejected by the timestamp anyway, so in production this is a Redis key with a
  5-minute TTL, not a set that grows forever. An in-memory set also forgets
  everything on restart and isn't shared between replicas.
- **The deeper fix is idempotency in the business logic:** "ship order X" should
  do nothing if X already shipped. Then a duplicate is harmless however it got in.
- **What this doesn't cover:** a leaked secret. Anyone holding it can sign
  anything. Rotate it like any other credential (lab 03's order: rotate first).
  Providers usually let two secrets be valid during a rotation.
- This is exactly how Stripe signs webhooks (`Stripe-Signature: t=…,v1=…`).
  GitHub uses `X-Hub-Signature-256` without a timestamp, so there the delivery ID
  is the only replay defence.
