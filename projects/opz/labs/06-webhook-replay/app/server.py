"""Shop backend: receives payment webhooks from the (fake) provider "Paylark".

When Paylark says a payment succeeded, the order is marked paid and shipped.
GET /orders shows what the shop believes happened.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8086"))
# Shared with Paylark when the webhook was registered. FAKE value, lab only.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "whsec_FAKE_lab06_do_not_use")

orders: dict[str, dict] = {
    "ord_1001": {"paid": False, "shipments": 0},
    "ord_1002": {"paid": False, "shipments": 0},
    "ord_1003": {"paid": False, "shipments": 0},
}


def handle_event(event: dict) -> None:
    if event.get("type") != "payment.succeeded":
        return
    order = orders.get(event["data"]["order_id"])
    if order is None:
        return
    order["paid"] = True
    order["shipments"] += 1
    print(f"shipped {event['data']['order_id']} (event {event.get('id')})", flush=True)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/orders":
            self._send(200, orders)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/webhook":
            self._send(404, {"error": "not found"})
            return
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))

        # Paylark sends "Paylark-Signature: t=<unix time>,v1=<hex HMAC-SHA256>".
        # TODO: verify it properly. For now just make sure it's there.
        if "Paylark-Signature" not in self.headers:
            self._send(400, {"error": "missing signature"})
            return

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            self._send(400, {"error": "bad json"})
            return
        handle_event(event)
        self._send(200, {"received": True})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"shop listening on 127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
