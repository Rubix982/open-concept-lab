"""Put the result files already on disk into the tidy table.

The tidy table is only useful if the runs that came before it are in it, and
most of them cannot be re-run cheaply. So each run's private shape is read once,
here, and converted. The conversion is per ticket because there is no shared
shape to discover — that absence is the reason `editreach.tidy` exists.

**Architecture is filled from a table, not guessed.** A result file records the
model's name and nothing about its shape, so `n_layers` would otherwise be
missing and every depth comparison with it would be impossible. The values below
are the served configs as `tools/ndif_catalogue.py` read them on 2026-11-15. A
model absent from the table gets empty columns rather than an assumed depth.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from editreach.tidy import Source, rows, write  # noqa: E402

RES = HERE.parents[1] / "results"
OUT = RES / "tidy"

#: (arch, n_layers, d_mlp) per model, from the served configs.
SHAPE: dict[str, tuple[str, int, int]] = {
    "EleutherAI/gpt-j-6b": ("gptj", 28, 16384),
    "meta-llama/Llama-3.1-8B": ("llama", 32, 14336),
    "meta-llama/Llama-3.1-70B": ("llama", 80, 28672),
}


def source(ticket: str, model: str, layer: int) -> Source:
    shape = SHAPE.get(model)
    if shape is None:
        return Source(ticket, model, layer)
    return Source(ticket, model, layer, *shape)


def from_e004(doc: dict) -> list[dict]:
    """E-004 keeps four parallel lists of per-question readings."""
    src = source("E-004", doc["model"], doc["layer"])
    pq = doc.get("per_question") or {}
    out: list[dict] = []
    for metric, values in pq.items():
        out += list(rows(src, "hop2", metric, values))
    return out


def from_e040(doc: dict) -> list[dict]:
    """E-040 keeps one dict per model, already the right granularity."""
    out: list[dict] = []
    for r in doc.get("rows", []):
        src = Source("E-040", r["model"], r["layer"], r.get("arch"),
                     r.get("n_layers"), r.get("d_mlp"))
        for metric in ("anchor_median", "anchor_min", "anchor_max",
                       "anchor_worst_deviation", "floor_median", "floor_min",
                       "floor_max", "separation"):
            if metric in r:
                group = "anchor" if metric.startswith("anchor") else "floor"
                out += list(rows(src, group, metric, [r[metric]], ["summary"]))
    return out


#: filename glob -> converter. Adding a ticket means adding a line and a
#: function, which is the honest cost of the shapes already being different.
CONVERTERS = {
    "E-004-far-field-floor*.json": from_e004,
    "E-040-*.json": from_e040,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    total = 0
    for pattern, fn in CONVERTERS.items():
        for path in sorted(RES.glob(pattern)):
            doc = json.loads(path.read_text())
            recs = fn(doc)
            if not recs:
                print(f"{path.name:<52} no per-item data, skipped")
                continue
            dest = a.out / (path.stem + ".csv")
            n = write(dest, recs)
            models = sorted({r["model"] for r in recs})
            print(f"{path.name:<52} {n:>6} rows  {', '.join(models)}")
            total += n
    print(f"\n{total} rows under {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
