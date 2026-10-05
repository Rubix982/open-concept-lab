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
