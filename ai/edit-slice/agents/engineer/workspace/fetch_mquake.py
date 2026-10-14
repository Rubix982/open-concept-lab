"""Fetch MQuAKE's released datasets. MIT licence, princeton-nlp/MQuAKE.

    .venv/bin/python agents/engineer/workspace/fetch_mquake.py

Runs [R-014]. Gitignored like the RippleEdits files, for the same reason: re-downloadable,
and this script rather than the bytes is the record of what was fetched and from where.
"""
from __future__ import annotations

import json
import os
import urllib.request

API = "https://api.github.com/repos/princeton-nlp/MQuAKE/contents/datasets"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DEST = os.path.join(ROOT, "data", "mquake")


def main() -> int:
    os.makedirs(DEST, exist_ok=True)
    with urllib.request.urlopen(API) as fh:
        listing = json.load(fh)
    got = 0
    for item in listing:
        name = item["name"]
        if not name.endswith(".json"):
            print(f"  skip  {name}")
            continue
        out = os.path.join(DEST, name)
        if os.path.exists(out) and os.path.getsize(out) == item["size"]:
            print(f"  have  {name}  {item['size']:,} bytes")
            got += 1
            continue
        print(f"  get   {name}  {item['size']:,} bytes")
        urllib.request.urlretrieve(item["download_url"], out)
        got += 1
    print(f"\n{got} file(s) in {os.path.relpath(DEST, ROOT)}")
    return 0 if got else 1


if __name__ == "__main__":
    raise SystemExit(main())
