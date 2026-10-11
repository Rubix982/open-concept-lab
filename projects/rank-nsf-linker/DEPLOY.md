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

**Cost:** about €8–13 a month (Hetzner, 8 GB: CX33, or Arm CAX21 when CX33 is sold out), or nothing
for the first 1–2.5 months on AWS's free plan (below), plus a domain (~$10 a year). Cloudflare,
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

### Or: the server on AWS's free plan (no money for the first 1–2.5 months)

New AWS accounts (on or after 15 July 2025) on the **Free plan** get $100 of credit, and up to $100
more for starter tasks, for 6 months. The account can't run up a bill: when the credit or the 6
months run out it stops. Charges are only possible after clicking "Upgrade to paid plan" — don't.
The one free-plan server with 8 GB is **m7i-flex.large** (2 vCPU, 8 GB): about $78 a month with
its disk and IPv4 address, so $100 lasts about 5 weeks and $200 about 2.5 months.

1. **Sign up** with the Free plan and Basic (free) support. Turn on MFA for the root user (top
   right → Security credentials → Assign MFA).
2. **Budget alert** (also one of the credit-earning tasks): Billing → Budgets → Create budget →
   "Zero spend budget", your email.
3. **Region** (top right): Asia Pacific (Mumbai), the nearest to Pakistan. If m7i-flex.large isn't
   offered there, Middle East (Bahrain) or Europe (Frankfurt).
4. **Your SSH key:** EC2 → Key pairs → Actions → Import key pair → name `atlas`, paste
   `~/.ssh/id_ed25519.pub`.
5. **EC2 → Launch instance:**
   - Name `atlas`; image **Ubuntu Server 24.04 LTS** (64-bit x86).
   - Type **m7i-flex.large** (marked "Free tier eligible").
   - Key pair `atlas`.
   - Network settings → Edit → create a security group `atlas` with one inbound rule:
     SSH, source **My IP**. This is temporary, for the first login only.
   - Storage: **60 GiB gp3**.
6. Launch. Copy the instance's **Public IPv4 address**, then from the laptop:
   `ssh ubuntu@<that address>` and do step 2 below. On AWS the user is `ubuntu`, so start with
   `sudo -i`, and after Docker is installed run `usermod -aG docker ubuntu`.
7. Once `tailscale up` works, **delete the SSH rule** from the `atlas` security group (EC2 →
   Security Groups → atlas → Inbound rules → Edit → Delete). Then nothing comes in, as on Hetzner.

To stop paying from the credit, **terminate** the instance (stopping it still charges for the disk
and IP address), then delete its volume and any leftover Elastic IP.

## 2. Server setup (once)

Until Tailscale is up you need SSH from Hetzner's web console (the firewall blocks port 22), or on
AWS the temporary SSH rule above:

```bash
apt update && apt -y upgrade && apt -y install unattended-upgrades
curl -fsSL https://tailscale.com/install.sh | sh && tailscale up --ssh   # then SSH over Tailscale
curl -fsSL https://get.docker.com | sh
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && systemctl restart ssh
```

## 3. Ship the code and the data (from your laptop)

A golden dataset that's already verified (e.g. `golden/2026-10-09/`, 9.4 GB) can be shipped as is;
`make golden` only makes a new one. The upload can take a few hours on a home connection: `-P`
lets an interrupted rsync pick up where it stopped. Disk at the peak is about 35 GB (database
15 GB, search indexes 6.4 GB, the shipped files, Docker images), so use at least 60 GB; delete
`ship/<date>` after step 4 to get 9 GB back. On AWS, first `sudo mkdir -p /srv/atlas && sudo chown
ubuntu /srv/atlas` on the server.

```bash
make golden                                   # only for a new one: postgres.dump + 2 Qdrant snapshots
rsync -aP --exclude data --exclude golden --exclude node_modules --exclude fresh ./ atlas:/srv/atlas/
rsync -aP data/scholarships golden/<date> atlas:/srv/atlas/ship/   # "atlas" = the server's Tailscale name
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
