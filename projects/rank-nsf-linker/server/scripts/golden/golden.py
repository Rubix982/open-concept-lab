"""Golden dataset: the finished state (everything fetched, loaded and embedded) as files, so a new
server restores it in minutes instead of fetching for days and embedding for hours.

    golden.py make     [--out golden/<date>]   dump Postgres + snapshot Qdrant + write manifest.json
    golden.py verify   <dir>                   restore into a scratch database and collection, compare
                                               counts with the manifest, then drop them (live data untouched)
    golden.py restore  <dir>                   restore into the live database and collection (stops
                                               go-server first, starts it after)

A golden directory holds postgres.dump (pg_dump custom format), qdrant-explorer_work.snapshot and
manifest.json (date, git commit, embedding model, row counts, fetch states, checksums). The dump
carries pipeline_status, so a restored server doesn't rebuild on start; data/ (raw downloads and
caches, ~22 GB) is not part of it. Runs on the host; needs docker and the dev compose stack.
Standard library only.
"""

import hashlib
from http.client import HTTPConnection
import json
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PG = "pg17-local"
DB = "rank-nsf-linker"
QDRANT = "http://localhost:6333"
EMBEDDER = "http://localhost:8000"
COLLECTION = "explorer_work"
PSQL = ["docker", "exec", "-i", "-e", "PGPASSWORD=postgres", PG]
COUNTS = {
    "people": "SELECT count(*) FROM explorer_faculty",
    "universities": "SELECT count(*) FROM explorer_universities",
    "grants": "SELECT count(*) FROM explorer_grants",
    "papers_and_grants_searchable": "SELECT count(*) FROM explorer_work_docs",
    "embedded": "SELECT count(*) FROM explorer_embedded",
}


def sh(cmd: list[str], **kw) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout.strip()


def psql(sql: str, db: str = DB) -> str:
    return sh(PSQL + ["psql", "-h", "localhost", "-U", "postgres", "-d", db, "-Atc", sql])


def http(method: str, url: str, body: bytes | None = None, headers: dict | None = None, timeout: int = 3600):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    return h.hexdigest()


def points(collection: str) -> int:
    return json.loads(http("GET", f"{QDRANT}/collections/{collection}"))["result"]["points_count"]


def make(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    status = psql("SELECT status FROM pipeline_status WHERE pipeline_name = 'populate_postgres'")
    if status != "completed":
        sys.exit(f"the pipeline is '{status}', not completed: finish it before making a golden dataset")
    print("postgres: dumping")
    dump = out / "postgres.dump"
    with dump.open("wb") as f:
        subprocess.run(PSQL + ["pg_dump", "-h", "localhost", "-U", "postgres", "-Fc", "-Z", "6", DB],
                       check=True, stdout=f)
    print("qdrant: snapshotting")
    name = json.loads(http("POST", f"{QDRANT}/collections/{COLLECTION}/snapshots?wait=true"))["result"]["name"]
    snap = out / f"qdrant-{COLLECTION}.snapshot"
    with urllib.request.urlopen(f"{QDRANT}/collections/{COLLECTION}/snapshots/{name}", timeout=3600) as r, \
            snap.open("wb") as f:
        while chunk := r.read(1 << 22):
            f.write(chunk)
    http("DELETE", f"{QDRANT}/collections/{COLLECTION}/snapshots/{name}")  # keep Qdrant's disk tidy

    fetch_state = {}
    for p in sorted((ROOT / "data" / "fetch_state").glob("*.json")):
        s = json.loads(p.read_text())
        fetch_state[p.stem] = {k: s.get(k) for k in ("status", "finished", "last_ok")}
    model = json.loads(http("GET", f"{EMBEDDER}/health")).get("model")
    manifest = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": sh(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "embedding_model": model,
        "counts": {k: int(psql(q)) for k, q in COUNTS.items()} | {"vectors": points(COLLECTION)},
        "fetch_state": fetch_state,
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in (dump, snap)},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest["counts"], indent=1))
    print(f"golden dataset: {out} ({sum(f['bytes'] for f in manifest['files'].values()) / 1e9:.1f} GB)")


def check_files(src: Path) -> dict:
    manifest = json.loads((src / "manifest.json").read_text())
    for name, meta in manifest["files"].items():
        if sha256(src / name) != meta["sha256"]:
            sys.exit(f"{name}: checksum does not match the manifest")
    return manifest


def restore_pg(src: Path, db: str) -> None:
    with (src / "postgres.dump").open("rb") as f:
        subprocess.run(PSQL + ["pg_restore", "-h", "localhost", "-U", "postgres", "-d", db, "--clean",
                               "--if-exists", "--no-owner", "--jobs", "1"], check=True, stdin=f,
                       stderr=subprocess.DEVNULL)


def restore_qdrant(src: Path, collection: str) -> None:
    """Upload the snapshot as a multipart form, streamed in chunks (a single 2 GB write fails)."""
    snap = src / f"qdrant-{COLLECTION}.snapshot"
    boundary = uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"snapshot\"; filename=\"{snap.name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    host = QDRANT.removeprefix("http://")
    conn = HTTPConnection(host, timeout=3600)
    conn.putrequest("POST", f"/collections/{collection}/snapshots/upload?priority=snapshot&wait=true")
    conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
    conn.putheader("Content-Length", str(len(head) + snap.stat().st_size + len(tail)))
    conn.endheaders()
    conn.send(head)
    with snap.open("rb") as f:
        while chunk := f.read(1 << 22):
            conn.send(chunk)
    conn.send(tail)
    resp = conn.getresponse()
    body = resp.read()
    if resp.status >= 300:
        sys.exit(f"qdrant snapshot upload: HTTP {resp.status} {body[:200]!r}")


def verify(src: Path) -> None:
    manifest = check_files(src)
    scratch_db, scratch_col = f"{DB}-golden-check", f"{COLLECTION}_golden_check"
    psql(f'DROP DATABASE IF EXISTS "{scratch_db}"', "postgres")
    psql(f'CREATE DATABASE "{scratch_db}"', "postgres")
    try:
        print("postgres: restoring into a scratch database")
        restore_pg(src, scratch_db)
        print("qdrant: restoring into a scratch collection")
        restore_qdrant(src, scratch_col)
        got = {k: int(psql(q, scratch_db)) for k, q in COUNTS.items()} | {"vectors": points(scratch_col)}
        bad = {k: (v, manifest["counts"][k]) for k, v in got.items() if v != manifest["counts"][k]}
        print(json.dumps(got, indent=1))
        print("verify: OK, counts match the manifest" if not bad else f"verify: MISMATCH {bad}")
        if bad:
            sys.exit(1)
    finally:
        psql(f'DROP DATABASE IF EXISTS "{scratch_db}"', "postgres")
        try:
            http("DELETE", f"{QDRANT}/collections/{scratch_col}")
        except OSError:
            pass


def restore(src: Path) -> None:
    check_files(src)
    compose = ["docker", "compose", "-f", str(ROOT / "docker-compose.dev.yaml")]
    print("stopping go-server")
    sh(compose + ["stop", "go-server"])
    try:
        print("postgres: restoring")
        restore_pg(src, DB)
        print("qdrant: restoring")
        restore_qdrant(src, COLLECTION)
    finally:
        print("starting go-server")
        sh(compose + ["start", "go-server"])
    print("restored")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("make", "verify", "restore"):
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "make":
        out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else \
            ROOT / "golden" / time.strftime("%Y-%m-%d")
        make(out)
    elif len(sys.argv) < 3:
        sys.exit(f"usage: golden.py {cmd} <golden dir>")
    elif cmd == "verify":
        verify(Path(sys.argv[2]))
    else:
        restore(Path(sys.argv[2]))


if __name__ == "__main__":
    main()
