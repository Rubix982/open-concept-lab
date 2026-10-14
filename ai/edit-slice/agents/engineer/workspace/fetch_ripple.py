"""Fetch the RippleEdits benchmark. MIT licence, edenbiran/RippleEdits.

    .venv/bin/python agents/engineer/workspace/fetch_ripple.py [--subset recent|random|popular|all]

Gitignored because they are ~11-20 MB each and re-downloadable; this script is the record
of exactly what was fetched and from where, which the files themselves are not.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request

API = "https://api.github.com/repos/edenbiran/RippleEdits/contents/data/benchmark"
# Four levels: workspace -> engineer -> agents -> the project root. Three put this in
# `agents/data/ripple`, where it silently succeeded and left `ripple_forms.py` reading a
# different directory than this script wrote — the two disagreed for a run and the
# measurement changed under it.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DEST = os.path.join(ROOT, "data", "ripple")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="all",
                    choices=["recent", "random", "popular", "all"])
    a = ap.parse_args()
    os.makedirs(DEST, exist_ok=True)
    with urllib.request.urlopen(API) as fh:
        listing = json.load(fh)
    for item in listing:
        name = item["name"]
        if a.subset != "all" and not name.startswith(a.subset):
            continue
        out = os.path.join(DEST, name)
        if os.path.exists(out) and os.path.getsize(out) == item["size"]:
            print(f"  have  {name}  {item['size']:,} bytes")
            continue
        # raw.githubusercontent 404s on a bare path for this repo; the API's download_url
        # is signed and works. Worth recording: a plain curl of the obvious URL returns
        # 14 bytes of "404: Not Found", which looks like an empty file, not an error.
        print(f"  get   {name}  {item['size']:,} bytes")
        urllib.request.urlretrieve(item["download_url"], out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
