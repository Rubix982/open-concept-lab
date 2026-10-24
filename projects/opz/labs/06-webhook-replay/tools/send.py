"""Send webhooks to the shop, as Paylark or as an attacker.

    python3 tools/send.py fresh  ord_1001   # a real, freshly signed event from Paylark
    python3 tools/send.py forge  ord_1002   # attacker: no secret, made-up signature
    python3 tools/send.py tamper ord_1003   # attacker: real signature, body edited after signing
    python3 tools/send.py stale  ord_1002   # attacker: a real event captured 10 minutes ago
    python3 tools/send.py replay            # attacker: resend the last real event, unchanged

Every real event is saved to tools/.last_event.json so `replay` can resend it,
the way an attacker who saw one request in a log or proxy could.
"""

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

URL = os.environ.get("SHOP_URL", "http://127.0.0.1:8086/webhook")
SECRET = os.environ.get("WEBHOOK_SECRET", "whsec_FAKE_lab06_do_not_use")
LAST = Path(os.environ.get("LAST_EVENT", Path(__file__).with_name(".last_event.json")))


def sign(body: bytes, ts: int, secret: str = SECRET) -> str:
    """Paylark's scheme: HMAC-SHA256 over "<timestamp>.<raw body>"."""
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def event_body(order_id: str, created: int | None = None) -> bytes:
    event = {
        "id": f"evt_{uuid.uuid4().hex[:16]}",
        "type": "payment.succeeded",
        "created": created or int(time.time()),
        "data": {"order_id": order_id, "amount": 4999, "currency": "usd"},
    }
    return json.dumps(event, separators=(",", ":")).encode()


def post(body: bytes, signature: str) -> tuple[int, str]:
    req = urllib.request.Request(
        URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "Paylark-Signature": signature},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else "fresh"
    order_id = sys.argv[2] if len(sys.argv) > 2 else "ord_1001"
    now = int(time.time())

    if kind == "fresh":
        body = event_body(order_id)
        sig = sign(body, now)
        LAST.write_text(json.dumps({"body": body.decode(), "sig": sig}))
    elif kind == "forge":
        body = event_body(order_id)
        sig = f"t={now},v1={'0' * 64}"
    elif kind == "tamper":
        real = event_body("ord_1001")
        sig = sign(real, now)
        body = real.replace(b"ord_1001", order_id.encode())
    elif kind == "stale":
        body = event_body(order_id, now - 600)
        sig = sign(body, now - 600)
    elif kind == "replay":
        saved = json.loads(LAST.read_text())
        body, sig = saved["body"].encode(), saved["sig"]
    else:
        sys.exit(__doc__)

    status, text = post(body, sig)
    print(f"{kind:7} -> HTTP {status} {text}")


if __name__ == "__main__":
    main()
