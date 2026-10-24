# Lab 08 · JWT Replay Due to No Expiry Validation

**Time:** ~40 min · **Needs:** Python 3 · **Cost:** free, all local

## The incident

Support reports refunds issued by a "user_42" who isn't an admin. The security
team also found a token in a log file from three months ago, and it still works.
And a token the auth server issued for the *billing* service is being accepted
by the *orders* service.

The orders API checks tokens in `app/auth.py`, hand-written "so we didn't need
another dependency".

## Setup

```bash
./setup.sh                        # makes .venv with PyJWT in it (you may want it)
source .venv/bin/activate
python app/server.py              # terminal 1: the API, on 127.0.0.1:8088
```

`tools/mint.py` makes tokens, honest and forged:

```bash
T=$(python tools/mint.py valid)
curl -s localhost:8088/me -H "Authorization: Bearer $T"
curl -s localhost:8088/admin/refunds -H "Authorization: Bearer $(python tools/mint.py none)"
```

Kinds: `valid`, `expired`, `wrong-aud`, `none`, `tampered`. Paste any token
into a decoder (or `python -c "import base64,sys; print(base64.urlsafe_b64decode(sys.argv[1]+'=='))" <middle part>`)
to see what's inside. A JWT is signed, not encrypted: anyone can read it.

## Your job

1. **Break it first.** Try each kind of token against `/me` and `/admin/refunds`.
   Which ones get in, and which one doesn't? Why does that one fail?
2. **Fix `app/auth.py`.** Hints, one at a time if you're stuck:
   - Who chooses `alg`, the server or the token? Who *should*?
   - Decode the `expired` token. Which claim says it's dead, and who reads it?
   - Same for `wrong-aud`: which claim names the service it was issued for?
   - You can repair the hand-written code, or replace it with `jwt.decode()` from
     PyJWT (already installed). Read what that function's `algorithms`,
     `audience`, `issuer` and `options={"require": [...]}` arguments do.
   - While you're in there, the signature comparison has a problem lab 06 also had.
3. **Prove it.** `./check.sh` starts its own copy on port 18088 and passes only
   when every bad token gets a 401 and an honest one still gets in.
4. **Write the retro** (below).

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- What's in a JWT, and what the signature does and doesn't protect:
- Why `alg: none` worked, and the one-line rule that stops it:
- Which claims must the API check itself, and what each one stops:
- Why the `tampered` token failed even before the fix:
- A leaked token is valid until `exp`. What keeps that window small in practice?
