# Deploying Advisor Atlas

One small server, nothing open to the internet. Visitors reach the site through Cloudflare, which
hides the server's address, absorbs attacks and handles HTTPS. You reach the server over Tailscale.
The data is built on your laptop and shipped as a golden dataset, so the server holds no API keys.

```
visitor ─HTTPS─> Cloudflare ─tunnel (outbound from the server)─> web (nginx) ─> go-server ─> Postgres
                                                                                         ├─> Qdrant
                                                                                         └─> embedder-lite
you ─Tailscale─> SSH
```

**Cost:** about €8–10 a month (Hetzner CX32, 8 GB) plus a domain (~$10 a year). Cloudflare,
Tailscale and an uptime check are free; Mapbox is free up to 50,000 map loads a month.

## 1. Accounts (once)

1. **Domain on Cloudflare** (free plan): add the domain, switch its nameservers to Cloudflare's.
2. **Tunnel:** Cloudflare dashboard → Zero Trust → Networks → Tunnels → Create a tunnel
   (Cloudflared). Copy the token from the install command. Add a public hostname:
   your domain → service `http://web:80`.
3. **Server:** Hetzner Cloud → CX32 (or CX22), Ubuntu 24.04, your SSH key. Under Firewalls, create one
   with **no inbound rules** and attach it to the server. Nothing needs to come in.
4. **Mapbox:** Account → Tokens → your public token → URL restrictions: add your domain (and
   `http://localhost` for local checks), so the token can't be reused elsewhere.

## 2. Server setup (once)

Until Tailscale is up you need SSH from Hetzner's web console (the firewall blocks port 22):

```bash
apt update && apt -y upgrade && apt -y install unattended-upgrades
curl -fsSL https://tailscale.com/install.sh | sh && tailscale up --ssh   # then SSH over Tailscale
curl -fsSL https://get.docker.com | sh
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && systemctl restart ssh
```

## 3. Ship the code and the data (from your laptop)

```bash
make golden                                   # golden/<date>/: postgres.dump + 2 Qdrant snapshots
rsync -a --exclude data --exclude golden --exclude node_modules --exclude fresh ./ atlas:/srv/atlas/
rsync -a data/scholarships golden/<date> atlas:/srv/atlas/ship/   # "atlas" = the server's Tailscale name
scp web/.env atlas:/srv/atlas/web/.env        # VITE_MAPBOX_TOKEN, built into the page
```

## 4. First start (on the server, in /srv/atlas)

```bash
cp .env.deploy.example .env.deploy && nano .env.deploy   # TUNNEL_TOKEN, a long POSTGRES_PASSWORD
mkdir -p data && cp -r ship/scholarships data/
C="docker compose -f docker-compose.minimal.yaml --env-file .env.deploy"
$C up -d postgres qdrant
$C exec -T postgres pg_restore -U postgres -d rank-nsf-linker --no-owner --clean --if-exists \
  < ship/<date>/postgres.dump
for c in explorer_work explorer_grants; do
  curl -X POST "http://127.0.0.1:6333/collections/$c/snapshots/upload?priority=snapshot" \
    -F "snapshot=@ship/<date>/qdrant-$c.snapshot"
done
$C --profile tunnel up -d --build
curl -s localhost:8088/api/explorer/funders | head -c 200   # the site, from the server itself
```

Then open your domain. Add a free uptime check (UptimeRobot or Cloudflare's health checks) on
`https://your.domain/api/explorer/funders`.

## Updating the data

On the laptop, refresh (the full stack does this on its own) and `make golden`; ship the new
`golden/<date>` (step 3), then on the server repeat the `pg_restore` and the two snapshot uploads,
and `$C restart go-server`. The previous golden dataset is your backup: restoring it rolls back.

## Updating the code

`git pull` (or rsync), then `$C --profile tunnel up -d --build`.

## What protects what

- **No open ports:** the cloud firewall has no inbound rules; the tunnel connects out. The server's
  address isn't in DNS, so attacks go to Cloudflare, not to it.
- **Inside:** Postgres, Qdrant, the embedder and the server are on Docker's private network. Only
  nginx is reachable, through the tunnel, and only `/api/` passes to the server.
- **Abuse limits:** nginx allows each visitor 20 API calls a second (bursts of 60) and 3 searches a
  second (bursts of 15); over that, a 429 and a "wait a few seconds" message. Cloudflare's dashboard
  can add stricter rules if needed (Security → WAF → Rate limiting rules).
- **Secrets:** only the tunnel token and the Postgres password, in `.env.deploy` on the server. The
  OpenAlex and KAKEN keys never leave your laptop; the Mapbox token is public by design and
  restricted to your domain.
