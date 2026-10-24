# Lab 16 · Solution (spoilers)

## What was happening

| Attack | What broke |
|---|---|
| `big 150` | `client_max_body_size 0` means "no limit", so NGINX passed 150 MB through. The app `read()` all of it into memory, then `json.loads` turned it into about 15 million Python strings, each far bigger than its few bytes on the wire. That went past the 256 MB limit, the kernel killed the process (exit 137), and Docker restarted it. Meanwhile NGINX returned 502 to everyone. |
| `nested 100000` | Python's JSON parser recurses once per bracket and gives up at about 1,000 levels with `RecursionError`. The handler thread died without a reply, so NGINX returned 502. It's tiny on the wire, and no size limit catches it. |
| `nested 800` | Gets past `json.loads`, then the app's own recursive `count_items` takes two stack frames per level and hits the same wall. |

## The fix: two layers

**NGINX** (`nginx/default.conf`):
```nginx
client_max_body_size 1m;
```
NGINX looks at `Content-Length` and answers `413 Request Entity Too Large` before
the body reaches the app. An upload endpoint that really needs more can get its
own `location` with a higher limit, rather than lifting it for everything.

**The app** (`app/app.py`):
```python
MAX_BODY = 1024 * 1024  # 1 MB; orders are a few KB
MAX_DEPTH = 32

        try:
            length = int(self.headers["Content-Length"])
        except (TypeError, ValueError):
            self._send(411, {"error": "Content-Length required"})
            return
        if length > MAX_BODY:
            self.close_connection = True  # don't read the body; just hang up after answering
            self._send(413, {"error": f"body over {MAX_BODY} bytes"})
            return
        raw = self.rfile.read(length)
        if not depth_ok(raw):
            self._send(400, {"error": f"nested deeper than {MAX_DEPTH}"})
            return
        try:
            order = json.loads(raw)
            items = count_items(order.get("items", []))
        except (ValueError, AttributeError, RecursionError):
            self._send(400, {"error": "bad order"})
            return
```

`depth_ok()` scans the bytes once, counting `[` and `{` outside strings, and
refuses anything deeper than 32. That's cheap, it runs before any parsing, and no
real order is nested that deep. The trap is brackets inside strings, like
`"note": "[[[["`, which is why it tracks quotes and backslashes:

```python
def depth_ok(raw: bytes, limit: int = MAX_DEPTH) -> bool:
    depth, in_str, escaped = 0, False, False
    for b in raw:
        if in_str:
            if escaped:
                escaped = False
            elif b == 0x5C:  # backslash
                escaped = True
            elif b == 0x22:  # quote
                in_str = False
        elif b == 0x22:
            in_str = True
        elif b in (0x5B, 0x7B):  # [ {
            depth += 1
            if depth > limit:
                return False
        elif b in (0x5D, 0x7D):  # ] }
            depth -= 1
    return True
```

## Why both layers

- The proxy limit protects the app from the internet. But anything already inside
  the network (another service, a misrouted internal call, a test script) reaches
  `app:8000` directly. `check.sh` does exactly that.
- The header check is free: the app answers 413 from `Content-Length` alone and
  never reads the 150 MB.
- No size limit stops the nested attack, because it's small. Only a structural
  limit (depth) or catching the error does.

## Details worth knowing

- **What this doesn't cover:** `Transfer-Encoding: chunked` has no
  `Content-Length`. This app now refuses those with 411. An app that accepts them
  has to count bytes while reading and stop at the limit. NGINX's
  `client_max_body_size` counts chunked bodies too.
- **Slow bodies:** an attacker can also send a small body very slowly and hold a
  worker open (Slowloris). That's `client_body_timeout` in NGINX and a socket
  timeout in the app, a separate defence.
- **Many valid requests:** 1,000 honest 1 MB orders a second is still a flood.
  That's rate limiting, another lab.
- **The memory limit did its job.** Without `mem_limit` the process would have
  kept growing into the host's memory, and the kernel might have killed something
  else. A limit turns "the machine fell over" into "one container restarted".
- Other parsers have the same limits under other names: `max_depth` in many JSON
  libraries, `MAX_CONTENT_LENGTH` in Flask, `client_max_body_size` in NGINX, body
  limits in Express (`express.json({limit})`).
