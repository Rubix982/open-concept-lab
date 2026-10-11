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
