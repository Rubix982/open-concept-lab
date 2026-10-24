"""Make tokens, honest and otherwise. Prints one token.

    python3 tools/mint.py valid       # what the auth server issues: 15 min, aud orders-api
    python3 tools/mint.py expired     # a real token that expired 90 days ago (found in an old log)
    python3 tools/mint.py wrong-aud   # a real token, but issued for billing-api
    python3 tools/mint.py none        # attacker: unsigned, alg "none", role admin
    python3 tools/mint.py tampered    # attacker: a real token with role edited to admin

Use it:  curl -s localhost:8088/me -H "Authorization: Bearer $(python3 tools/mint.py valid)"
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time

SECRET = os.environ.get("JWT_SECRET", "jwt_FAKE_lab08_signing_key_do_not_use").encode()
ISSUER = "https://auth.opz.local"


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def encode(header: dict, claims: dict, key: bytes | None) -> str:
    signing_input = f"{b64(json.dumps(header).encode())}.{b64(json.dumps(claims).encode())}"
    sig = b64(hmac.new(key, signing_input.encode(), hashlib.sha256).digest()) if key else ""
    return f"{signing_input}.{sig}"


def claims(role: str = "customer", aud: str = "orders-api", issued: int | None = None, ttl: int = 900) -> dict:
    iat = issued if issued is not None else int(time.time())
    return {"iss": ISSUER, "sub": "user_42", "aud": aud, "role": role, "iat": iat, "exp": iat + ttl}


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else "valid"
    hs = {"alg": "HS256", "typ": "JWT"}
    if kind == "valid":
        token = encode(hs, claims(), SECRET)
    elif kind == "expired":
        token = encode(hs, claims(issued=int(time.time()) - 90 * 86400), SECRET)
    elif kind == "wrong-aud":
        token = encode(hs, claims(aud="billing-api"), SECRET)
    elif kind == "none":
        token = encode({"alg": "none", "typ": "JWT"}, claims(role="admin"), None)
    elif kind == "tampered":
        real = encode(hs, claims(), SECRET)
        header_b64, _, sig = real.split(".")
        token = f"{header_b64}.{b64(json.dumps(claims(role='admin')).encode())}.{sig}"
    else:
        sys.exit(__doc__)
    print(token)


if __name__ == "__main__":
    main()
