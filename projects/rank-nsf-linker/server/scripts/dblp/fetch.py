"""DBLP dump -> data/dblp/dblp.xml.gz and dblp.dtd (CC0), refreshed monthly.

The "Load DBLP Papers" pipeline step reads the dump. It is about 1 GB; a download that fails keeps
the previous copy.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fetchlib import ROOT, download  # noqa: E402

OUT = ROOT / "data" / "dblp"


def main() -> None:
    download("https://dblp.org/xml/dblp.dtd", OUT / "dblp.dtd", max_age_days=30)
    if download("https://dblp.org/xml/dblp.xml.gz", OUT / "dblp.xml.gz", max_age_days=30, timeout=3600):
        print("data/dblp/dblp.xml.gz: new dump")
    else:
        print("data/dblp/dblp.xml.gz: current (under 30 days old)")


if __name__ == "__main__":
    main()
