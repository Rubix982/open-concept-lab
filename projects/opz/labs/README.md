# opz labs

Bite-sized, standalone versions of the scenarios in `../devops_scenarios.md`.
Each lab is one folder: break → diagnose → fix → prove → retro. Nothing here
depends on any other project.

Every lab has the same parts:
- `README.md` — the incident, your job, hints, a 5-line retro to fill in
- `app/` — the smallest stack that reproduces the problem
- `check.sh` — passes only when the problem is truly fixed
- `SOLUTION.md` — spoilers, read last

| # | Lab | Needs | Status |
|---|-----|-------|--------|
| 01 | [Hardcoded Credentials in Dockerfile](01-hardcoded-creds-dockerfile/) | Docker | solved |
| 02 | [Secret Exposed Through Environment Variables](02-env-var-secret-exposure/) | Docker Compose | solved |
| 03 | [Secret Committed to a Repo](03-secret-committed-to-repo/) | git, gitleaks, git-filter-repo | solved |
| 04 | [Debugging a CrashLoopBackOff Pod](04-crashloopbackoff/) | Docker, kind, kubectl | solved |
| 05 | [Resource Starvation due to Misconfigured Requests & Limits](05-oomkilled/) | Docker, kind, kubectl | ready |
| 06 | [Replay Attack via Insecure Webhooks](06-webhook-replay/) | Python | ready |
| 07 | [Graceful Shutdown (PID 1 ignores SIGTERM)](07-graceful-shutdown/) | Docker | ready |
| 08 | [JWT Replay Due to No Expiry Validation](08-jwt-validation/) | Python | ready |
| 09 | [Unsecured Redis Allows Remote Access](09-unsecured-redis/) | Docker Compose | ready |
| 10 | [Credential Rotations Not Propagated](10-credential-rotation/) | Docker Compose, Python | ready |
| 11 | [Escalating Build Times Due to Dependency Bloat](11-image-bloat/) | Docker | ready |
| 12 | [Pod Crash on Timezone Mismatch](12-timezone-mismatch/) | Docker | ready |
| 13 | [Forgotten Default Credentials](13-default-credentials/) | Docker Compose | ready |
| 14 | [Post-Deployment Failure Due to Missing Migration](14-missing-migration/) | Docker Compose, Postgres | ready |
| 15 | [Rate Limiting Not Enforced on Public API](15-rate-limiting/) | Docker Compose, NGINX | ready |
| 16 | [DoS Attack via Large JSON Body](16-large-json-dos/) | Docker Compose, NGINX | ready |
| 17 | [Log Injection Attack on Centralized Logging](17-log-injection/) | Python | ready |
| 18 | [Silent Data Loss from Wrong Volume Mount](18-volume-data-loss/) | Docker, kind, kubectl | ready |
| 19 | [Alert Not Fired Due to Misconfigured Label](19-alert-label/) | Docker Compose, Prometheus | ready |
