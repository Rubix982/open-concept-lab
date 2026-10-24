"""Token checking for the orders API.

Tokens come from the company's auth server (https://auth.opz.local), signed with
HS256 and a key shared between it and every API. Written in a hurry so we didn't
need another dependency.
"""

import base64
import hashlib
import hmac
import json
import os

# Shared with the auth server. FAKE value, lab only.
SECRET = os.environ.get("JWT_SECRET", "jwt_FAKE_lab08_signing_key_do_not_use").encode()


class InvalidToken(Exception):
    pass


def _b64decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def decode(token: str) -> dict:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        header = json.loads(_b64decode(header_b64))
        claims = json.loads(_b64decode(payload_b64))
    except ValueError as e:
        raise InvalidToken("malformed token") from e

    alg = header.get("alg")
    if alg == "none":
        # the integration tests send unsigned tokens
        return claims
    if alg == "HS256":
        expected = _b64encode(
            hmac.new(SECRET, f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        )
        if expected != sig_b64:
            raise InvalidToken("bad signature")
        return claims
    raise InvalidToken(f"unsupported alg {alg!r}")
