# Lab 08 · Solution (spoilers)

## What was wrong

A JWT is three base64 parts, `header.claims.signature`. The hand-written
`decode()` made three mistakes:

| Token | Why it got in |
|---|---|
| `none` | The code let **the token** pick the algorithm, and `none` meant "skip the signature". An attacker writes any claims they like, including `role: admin`. |
| `expired` | Nothing read `exp`. A signature never expires; the claim does, but only if someone checks it. |
| `wrong-aud` | Nothing read `aud`. The auth server signs tokens for every service with the same key, so a billing token is "valid" everywhere unless each API checks it was meant for *it*. |

`tampered` failed even before the fix: editing the claims breaks the HS256
signature, and that branch did check it. The signature code was fine. The problem
was everything around it.

## The fix

Use a library that already checks everything, and pin the algorithm:

```python
import jwt

SECRET = os.environ.get("JWT_SECRET", "jwt_FAKE_lab08_signing_key_do_not_use")


def decode(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET,
            algorithms=["HS256"],                 # the server decides, never the token
            audience="orders-api",                # issued for *this* service
            issuer="https://auth.opz.local",      # by *our* auth server
            options={"require": ["exp", "iat", "aud", "iss", "sub"]},  # missing claim = reject
            leeway=30,                            # tolerate a little clock skew
        )
    except jwt.InvalidTokenError as e:
        raise InvalidToken(str(e)) from e
```

`require` matters: without it, a token that simply *leaves out* `exp` is never
checked for expiry.

If you repaired the hand-written version instead, it needs: reject any `alg`
other than HS256, `hmac.compare_digest` for the signature, and checks for `exp`
(with leeway), `aud` and `iss`.

## Details worth knowing

- **Pin the algorithm.** The classic follow-up to `alg: none` is algorithm
  confusion: a server expecting RS256 (public/private keys) is sent an HS256 token
  "signed" with the *public* key, which is public. `algorithms=[...]` stops both.
- **Short lifetimes, not revocation.** You usually can't revoke a JWT, because the
  API never asks the auth server about it. So access tokens live minutes, and a
  long-lived *refresh token*, stored server-side where it can be revoked, gets new ones.
- **Shared HMAC keys are a weak spot.** Every API that can *verify* HS256 tokens
  can also *mint* them. With RS256/ES256 only the auth server holds the private
  key, and APIs get the public one (often from a JWKS URL).
- **Don't log tokens.** The 90-day-old token came from a log. Log the `jti` or
  `sub`, never the bearer string.
