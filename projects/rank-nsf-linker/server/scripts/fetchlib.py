"""Helpers the fetch scripts share: secrets, downloads, and the exit code for a partial run.

The pipeline runs every fetch script through the fetcher container (fetcher/app.py). A script
exits 0 when its output is complete, PARTIAL (75) when it stopped early on purpose (a daily API
allowance, say) and should simply run again later, and anything else on failure. Outputs are
replaced only when complete, so a failed or partial run never removes good data.
Standard library only.
"""

import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTIAL = 75  # EX_TEMPFAIL: stopped early, run again later
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}


def secret(name: str) -> str:
    """An API key from the environment (the fetcher container), else server/.env (a developer's
    machine). Never printed."""
    value = os.environ.get(name, "").strip()
    if value:
        return value
    env = ROOT / "server" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(f"{name} is not set (environment or server/.env)")


def fresh(path: Path, max_age_days: float) -> bool:
    return path.exists() and path.stat().st_size > 0 and time.time() - path.stat().st_mtime < max_age_days * 86400


def download(url: str, dest: Path, max_age_days: float = 30, timeout: int = 600) -> bool:
    """Download url to dest unless dest is younger than max_age_days. Written to a temporary file
    and renamed when complete, so an interrupted download never leaves a broken file behind.
    Returns True when it downloaded."""
    if fresh(dest, max_age_days):
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r, \
                    tmp.open("wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            tmp.replace(dest)
            print(f"  downloaded {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
            return True
        except (urllib.error.URLError, OSError) as e:
            if attempt == 3:
                tmp.unlink(missing_ok=True)
                if dest.exists():
                    print(f"  {dest.name}: download failed ({e}); keeping the copy from before")
                    return False
                sys.exit(f"{dest.name}: download failed: {e}")
            time.sleep(15 * (attempt + 1))
    return False


# ---- OpenAlex snapshots (s3://openalex/data/jsonl/<entity>/, CC0, no API calls) ----
# S3's IPv4 route can be very slow from some networks; the dual-stack endpoint is tried first.
OPENALEX_HOSTS = ["https://openalex.s3.dualstack.us-east-1.amazonaws.com/", "https://openalex.s3.amazonaws.com/"]


def _snapshot_file(key: str, dest: Path, size: int | None) -> bool:
    """Download one snapshot file (atomic); True when dest is complete."""
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    for attempt in range(6):
        host = OPENALEX_HOSTS[attempt % len(OPENALEX_HOSTS)]
        try:
            with urllib.request.urlopen(host + key, timeout=120) as r, tmp.open("wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if size is not None and tmp.stat().st_size != size:
                raise OSError(f"got {tmp.stat().st_size} bytes, expected {size}")
            tmp.replace(dest)
            return True
        except OSError as e:
            print(f"  {key}: {type(e).__name__} {e} (attempt {attempt + 1})", flush=True)
            time.sleep(10 * (attempt + 1))
    tmp.unlink(missing_ok=True)
    return False


def openalex_snapshot(entity: str) -> list[Path]:
    """The files of an OpenAlex snapshot entity ("awards", "institutions") in data/openalex_<entity>/,
    downloading new or changed ones (by the manifest's sizes). Exits PARTIAL when some failed."""
    import json
    from concurrent.futures import ThreadPoolExecutor
    prefix, cache = f"data/jsonl/{entity}/", ROOT / "data" / f"openalex_{entity}"
    manifest = None
    for host in OPENALEX_HOSTS:
        try:
            with urllib.request.urlopen(host + prefix + "manifest.json", timeout=120) as r:
                manifest = json.loads(r.read())
            break
        except OSError:
            continue
    if manifest is None:
        sys.exit(f"OpenAlex {entity} manifest unreachable")
    files = []
    for e in manifest.get("files") or manifest.get("entries") or []:
        key = e["url"].split("s3://openalex/", 1)[1]
        files.append((key, cache / key.removeprefix(prefix), (e.get("meta") or {}).get("content_length")))
    todo = [f for f in files if not (f[1].exists() and (f[2] is None or f[1].stat().st_size == f[2]))]
    print(f"OpenAlex {entity}: {len(files)} snapshot files, {len(todo)} to download "
          f"({sum(f[2] or 0 for f in todo) / 1e9:.1f} GB)", flush=True)
    done, start = 0, time.time()
    with ThreadPoolExecutor(4) as pool:
        for ok in pool.map(lambda f: _snapshot_file(*f), todo):
            done += 1
            if done % 10 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time() - start:.0f} s)", flush=True)
    keep = {f[1] for f in files}
    for old in cache.rglob("*.gz"):
        if old not in keep:
            old.unlink()  # files the snapshot no longer lists
    if any(not f[1].exists() for f in files):
        print(f"OpenAlex {entity}: some files missing; rerun to resume")
        sys.exit(PARTIAL)
    return [f[1] for f in files]


def snapshot_records(paths: list[Path]):
    import gzip
    import json
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)
