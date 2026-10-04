"""Parse ERC "List of Principal Investigators" PDFs (Horizon Europe calls) into rows.

The ERC publishes, per call, a PDF table: last name, first name, host institution (English and local
name), host country, acronym, title, panel. pdftotext -layout keeps the columns; long cells wrap onto
lines above and below the line that carries the panel code. Each record is the panel line plus the
wrapped lines up to halfway to its neighbours, cut into columns at the header's positions.
"""

import re
import subprocess
from pathlib import Path

PANEL = re.compile(r"\b((?:PE|LS|SH)\d{1,2})\s*$")
FOOTER = re.compile(r"erc\.europa\.eu|European Research Council|Page \d+ of \d+", re.I)


def columns(lines: list[str]) -> list[tuple[str, int]] | None:
    """Column starts, left to right. The header line names last/first name, the English institution
    name, acronym, title and panel; the line above names the local institution name and "Host"
    (country). Their order differs between years, so columns are sorted by position."""
    for i, line in enumerate(lines):
        labels = {"last": "last name", "first": "first name", "inst": "host institution name",
                  "acronym": "acronym", "title": "title", "panel": "panel"}
        low = line.lower()
        if not all(v in low for v in labels.values()):
            continue
        cols = {k: low.index(v) for k, v in labels.items()}
        for j in range(max(0, i - 2), i):
            above = lines[j].lower()
            k = above.find("host institution local")
            if k >= 0:
                cols["local"] = k
                # "Host" (country) is the next "host" after the local-name label
                c = above.find("host", k + len("host institution local"))
                if c >= 0:
                    cols["country"] = c
        return sorted(cols.items(), key=lambda kv: kv[1])
    return None


def cell(line: str, start: int, end: int) -> str:
    return line[start:end].strip() if len(line) > start else ""


def parse_pdf(path: Path) -> list[dict]:
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                          check=True).stdout
    rows = []
    for page in text.split("\f"):
        lines = page.splitlines()
        cols = columns(lines)
        if not cols:
            continue
        bounds = {name: (pos, cols[k + 1][1] if k + 1 < len(cols) else 10_000)
                  for k, (name, pos) in enumerate(cols)}
        start = next(i for i, l in enumerate(lines) if "last name" in l.lower() and "panel" in l.lower()) + 1
        body = [l for l in lines[start:] if not FOOTER.search(l)]
        anchors = [i for i, l in enumerate(body) if PANEL.search(l) and len(l) > bounds["panel"][0] - 5]
        for n, a in enumerate(anchors):
            lo = 0 if n == 0 else (anchors[n - 1] + a) // 2 + 1
            hi = len(body) if n == len(anchors) - 1 else (a + anchors[n + 1]) // 2 + 1
            part = body[lo:hi]

            def joined(name: str) -> str:
                if name not in bounds:
                    return ""
                s0, s1 = bounds[name]
                return re.sub(r"\s+", " ", " ".join(cell(l, s0, s1) for l in part)).strip()

            country = re.findall(r"\b([A-Z]{2})\b", joined("country")) if "country" in bounds else []
            rows.append({
                "last": joined("last"), "first": joined("first"), "institution": joined("inst"),
                "country": country[0] if country else "",
                "acronym": cell(body[a], *bounds["acronym"]) or joined("acronym"),
                "title": joined("title"), "panel": PANEL.search(body[a]).group(1),
            })
    return rows


if __name__ == "__main__":
    import sys
    for r in parse_pdf(Path(sys.argv[1]))[:12]:
        print(r)
