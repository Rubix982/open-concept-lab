"""Pivot the tidy table into the per-model table a paper prints.

The tidy table is one row per measurement, which is right for storage and
useless to read. This collapses it the one way the per-family model rule asks
for: **one row per model**, the quantities across, and the model's depth beside
the layer so two rows can honestly be compared.

It reports a median and a count, never a mean. The readings are coefficients
bounded below by zero with a long right tail, and a mean on those moves with
whichever probe happened to land highest.
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from editreach.tidy import combine  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tidy", type=Path, default=HERE.parents[1] / "results" / "tidy")
    ap.add_argument("--ticket", help="only this ticket")
    ap.add_argument("--metrics", nargs="*", help="only these metrics, in this order")
    a = ap.parse_args()

    recs = [r for r in combine(a.tidy) if r["value"] is not None]
    if a.ticket:
        recs = [r for r in recs if r["ticket"] == a.ticket]
    if not recs:
        print("no rows")
        return 1

    cells: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in recs:
        key = (r["ticket"], r["model"], r["n_layers"], r["layer"],
               r["depth_fraction"])
        cells[key][r["metric"]].append(r["value"])

    metrics = a.metrics or sorted({r["metric"] for r in recs})
    wm = max(len(k[1]) for k in cells)
    head = (f"{'ticket':<7} {'model':<{wm}} {'layers':>6} {'L':>3} {'depth':>6}  "
            + "  ".join(f"{m[:14]:>14}" for m in metrics))
    print(head)
    print("-" * len(head))
    # Sorted by where the layer sits, not by the layer number: the whole point
    # is that layer 5 is not one place.
    for key in sorted(cells, key=lambda k: (k[0], k[4] or 0, k[1])):
        ticket, model, n_layers, layer, depth = key
        line = (f"{ticket:<7} {model:<{wm}} {n_layers or '?':>6} {layer:>3} "
                f"{(f'{depth:.3f}' if depth is not None else '?'):>6}  ")
        for m in metrics:
            v = cells[key].get(m)
            line += f"{(f'{st.median(v):.4f}' if v else '—'):>14}  "
        print(line)

    print()
    for m in metrics:
        n = sum(len(c.get(m, [])) for c in cells.values())
        print(f"  {m:<24} {n:>6} readings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
