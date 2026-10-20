# Holding page

What advisoratlas.fyi shows while the server is off: one short page that says the
app is paused and links to the write-up. It is a Cloudflare Worker (`worker.js`),
free on Cloudflare's plan, and needs nothing running anywhere else.

## Turn it on (dashboard, about five minutes)

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Create Worker**.
   Name it `advisoratlas-paused`, then **Deploy**.
2. **Edit code**, replace everything with the contents of `worker.js`, **Deploy**.
3. In the worker: **Settings** → **Domains & Routes** → **Add** → **Route**.
   Zone `advisoratlas.fyi`, route `advisoratlas.fyi/*`. If `www` exists, add
   `www.advisoratlas.fyi/*` too.
4. Open https://advisoratlas.fyi. You should see the holding page.
5. Stop the server.

Use a **route**, not a custom domain. The existing DNS record (the tunnel's
proxied CNAME) stays where it is. The route answers every request before
Cloudflare tries the tunnel, so the app never sees traffic.

## Turn it off

Delete the route (or the worker), start the server, and the tunnel serves the
app again. Nothing in DNS changed, so there is nothing else to undo.
