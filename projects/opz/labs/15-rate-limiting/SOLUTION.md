# Lab 15 · Solution (spoilers)

## What was wrong

Nothing limited anyone. The database has 4 connections, so the API is a queue,
and the scraper's 40 threads kept it full. Alice's request waited in line
behind dozens of the scraper's. The API wasn't broken, just shared unfairly.

## The fix

In `nginx/nginx.conf`, inside `http { }`:

```nginx
    # Limit per API key; callers without a key are limited per IP.
    map $http_x_api_key $limit_key {
        ""      $binary_remote_addr;
        default $http_x_api_key;
    }
    limit_req_zone $limit_key zone=per_key:10m rate=10r/s;
```

and in `server { }`:

```nginx
        error_page 429 = @too_many;
        location @too_many {
            add_header Retry-After 1 always;
            default_type application/json;
            return 429 '{"error": "too many requests"}\n';
        }

        location / {
            limit_req zone=per_key burst=20 nodelay;
            limit_req_status 429;
            proxy_pass http://api;
            ...
        }
```

Result in the check: the scraper got 429 on ~99% of its requests, and Alice's
p95 latency went from ~700 ms to ~60 ms.

## The pieces

- **`limit_req_zone`** defines the bucket: what it's keyed by, 10 MB of shared
  memory for the counters (about 160k keys), and the rate.
- **The key.** Behind Docker, a NAT or a corporate proxy, many customers share one
  IP, so limiting by IP punishes the wrong people. Limit by what identifies the
  customer, which is the API key, and fall back to IP for anonymous traffic.
  (An empty key isn't counted at all by `limit_req_zone`, hence the `map`.)
- **Leaky bucket.** `rate=10r/s` means one request every 100 ms. `burst=20` lets up
  to 20 extra wait in line instead of being rejected, and `nodelay` serves those 20
  at once instead of spacing them out. So a client gets an initial burst, then a
  steady 10/s. That's why the scraper still got about 100 successes in 8 seconds.
- **`limit_req_status 429`.** NGINX rejects with **503** by default. 503 says "the
  server is broken", which sets off your alerts and makes clients retry harder. 429
  says "*you* are sending too much".
- **`Retry-After`** tells a well-behaved client when to try again. NGINX doesn't add
  it on its own; the named location does.

## Details worth knowing

- **Several NGINX instances each count separately.** With 3 proxies, a client gets
  3× the limit. For an exact global limit, count in a shared store (Redis), as API
  gateways do. Per-instance limits are often good enough.
- **Limit concurrency too.** `limit_conn` caps open connections per key. It catches
  slow, expensive requests that a requests-per-second limit lets through.
- **Different endpoints need different limits.** Login and password-reset want a
  much stricter limit, keyed by account as well as by IP.
- **What this doesn't cover:** a real DDoS from many IPs with no key fills the
  network before NGINX can say no; that's handled upstream (CDN, provider). And a
  scraper that rotates through many stolen or free keys needs per-account quotas
  and abuse detection, not a proxy rule.
- The half-fix to watch for: adding `limit_req` and stopping. The scraper is
  slowed, but it gets 503s with no `Retry-After`, and your error dashboards light up.
