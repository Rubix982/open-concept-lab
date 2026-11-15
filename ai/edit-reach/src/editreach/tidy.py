"""One long-format table every run writes into, so a chart never parses a run file.

Each run script grew its own result shape. `E-004` keeps four parallel lists of
900 under `per_question`; `E-040` keeps a list of per-model dicts; `E-003` keeps
something else again. Every figure tool therefore opens one named file and digs
through that file's private layout, which has two costs. A new chart needs new
parsing code before it can be drawn, and a chart **cannot span two runs at all**
— which is exactly what the per-family model rule now asks for.

So runs also write here, in long format: one row per measurement, never per
item. Columns are fixed and every row carries the model it came from.

    ticket  model  arch  n_layers  d_mlp  layer  depth_fraction
    group   item_id  metric  value

`group` is the run's own partition — a probe family, a hop, an arm. `metric`
names the quantity, `value` is the number, and nothing else is a column. A new
quantity is a new value of `metric`, not a new column, so the schema does not
move when a run starts reporting something extra.

**Why the model's shape is on every row rather than in a header.** Layer 5 is
16% of the way through a 32-layer model and 6% through an 80-layer one. A table
that records the layer without the depth cannot be compared across models, and
the comparison will be attempted anyway — so `n_layers` and `depth_fraction`
travel with each measurement instead of being recoverable from somewhere else.

This is a record, not an analysis. Medians, bootstraps and gates stay in the run
scripts; everything here is a raw reading with its provenance attached.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

#: Fixed column order. Anything appended to a tidy file must match it, so the
#: files concatenate without a header negotiation.
COLUMNS: tuple[str, ...] = (
    "ticket", "model", "arch", "n_layers", "d_mlp", "layer", "depth_fraction",
    "group", "item_id", "metric", "value",
)


@dataclass(frozen=True, slots=True)
class Source:
    """What produced a measurement: the run, the model, and where it was read.

    `arch`, `n_layers` and `d_mlp` come from `editreach.arch.resolve_arch`, so
    they are read off the served config rather than inferred from the name.
    They are optional only because a backfill of an old result file has no
    model to ask.
    """

    ticket: str
    model: str
    layer: int
    arch: str | None = None
    n_layers: int | None = None
    d_mlp: int | None = None

    @property
    def depth_fraction(self) -> float | None:
        """Where in the model this layer sits, as a fraction of its depth."""
        return self.layer / self.n_layers if self.n_layers else None

    @classmethod
    def resolved(cls, ticket: str, model, name: str, layer: int) -> "Source":
        """Build one from a connected model, reading its architecture."""
        from .arch import resolve_arch
        arch, n_layers, d_mlp = resolve_arch(model, name)
        return cls(ticket, name, layer, arch, n_layers, d_mlp)


def rows(src: Source, group: str, metric: str,
         values: Sequence[float | None],
         item_ids: Sequence[str] | None = None) -> Iterator[dict]:
    """One row per value. `item_ids` defaults to the position in `values`.

    A `None` value is kept rather than dropped: a probe that could not be read
    is a fact about coverage, and a chart that silently has fewer points than
    the run claims is worse than one with a gap in it.
    """
    if item_ids is not None and len(item_ids) != len(values):
        raise ValueError(f"{len(item_ids)} ids against {len(values)} values")
    head = {
        "ticket": src.ticket, "model": src.model, "arch": src.arch,
        "n_layers": src.n_layers, "d_mlp": src.d_mlp, "layer": src.layer,
        "depth_fraction": (None if src.depth_fraction is None
                           else round(src.depth_fraction, 4)),
        "group": group, "metric": metric,
    }
    for i, v in enumerate(values):
        yield {**head,
               "item_id": item_ids[i] if item_ids is not None else str(i),
               "value": v}


def write(path: Path, records: Iterable[dict], *, append: bool = False) -> int:
    """Write (or append) rows as CSV. Returns how many were written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    n = 0
    with path.open("a" if append else "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="raise")
        if not (append and exists):
            w.writeheader()
        for r in records:
            w.writerow(r)
            n += 1
    return n


def read(path: Path) -> list[dict]:
    """Rows back, with the numeric columns as numbers and blanks as `None`."""
    ints = {"n_layers", "d_mlp", "layer"}
    floats = {"depth_fraction", "value"}
    out = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            for k in ints:
                r[k] = int(r[k]) if r[k] not in ("", None) else None
            for k in floats:
                r[k] = float(r[k]) if r[k] not in ("", None) else None
            for k, v in r.items():
                if v == "":
                    r[k] = None
            out.append(r)
    return out


def combine(directory: Path) -> list[dict]:
    """Every tidy CSV under `directory`, as one list. This is what a chart reads."""
    out: list[dict] = []
    for p in sorted(directory.glob("*.csv")):
        out.extend(read(p))
    return out
