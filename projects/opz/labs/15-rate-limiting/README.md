# Lab 15 · Rate Limiting Not Enforced on Public API

**Time:** ~30 min · **Needs:** Docker Compose (NGINX and the API run in containers) · **Cost:** free, all local

## The incident

The product-search API sits behind NGINX. Customers authenticate with an
`X-API-Key` header. Since this morning one customer's scraper has been hammering
`/search` as fast as it can. Every other customer's searches now take most of a
second, and support is getting "is the site down?" tickets. The database has only
4 connections, and the scraper is holding all of them.

## Setup

```bash
./setup.sh                    # API behind nginx on localhost:8015
python3 tools/load.py         # 6 s: a 40-thread scraper and Alice (5 req/s), with a summary
docker compose logs -f proxy  # every request: key, status, time taken
```

After editing `nginx/nginx.conf`: `docker compose exec proxy nginx -s reload`
(or re-run `./setup.sh`). A syntax error makes the reload fail and print why.

## Your job

1. **Break it first.** Run `tools/load.py`. What are Alice's latencies with and
   without the scraper running? (`curl` her on her own for a baseline.)
2. **Limit each customer in `nginx/nginx.conf`.** Hints, one at a time:
   - Read about NGINX's `limit_req_zone` and `limit_req`. One defines the limit
     and what it is counted by, the other applies it to a location.
   - Count by what? Every request here comes from the same IP (Docker's network).
     What identifies a customer? What about callers who send no key?
   - With only a rate, a client that sends 3 requests at once gets 2 rejected.
     Look up `burst` and `nodelay`.
   - What status does NGINX send by default when it rejects? Is that the right one?
     What should a well-behaved client be told about *when* to come back?
3. **Prove it.** `./check.sh` starts its own copy on port 18015 with your config
   and floods it for 8 seconds. It passes only when the scraper mostly gets `429`
   with a `Retry-After` header, and Alice is never refused and stays under 150 ms.
4. **Write the retro** (below).
5. **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why one client slowed down everyone:
- What I limited by, and why not IP here:
- What `rate`, `burst` and `nodelay` each do:
- Why 429 and not 503, and what `Retry-After` is for:
- What a proxy rate limit doesn't protect against:
