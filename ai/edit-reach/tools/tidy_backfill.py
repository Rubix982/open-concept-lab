"""Put every value in every result file already on disk into the tidy table.

The tidy table is only worth having if the runs that came before it are in it,
and most cannot be re-run cheaply. Each run's private shape is read once, here,
and converted. The conversion is per ticket because there is no shared shape to
discover — that absence is the reason `editreach.tidy` exists.

Two layers of capture, and the second is what makes "every value" true rather
than aspirational:

1. **Per-item converters** for the files that hold arrays — the 495 probes, the
   900 far-field questions, the 1,539 bound readings, the conformance checks,
   the layer sweeps. These carry the distributions a chart is drawn from.
2. **A scalar sweep** over whatever the converters did not claim. Every number
   left at any depth of the document becomes a row under the group `summary`,
   keyed by its dotted path. It is unglamorous and it is the half that stops a
   headline figure from living only in a log line.

**Architecture is filled from a table, not guessed.** A result file records the
model's name and nothing about its shape, so `n_layers` would otherwise be
missing and every depth comparison with it impossible. The values below are the
served configs as `tools/ndif_catalogue.py` read them on 2026-11-15. A model
absent from the table gets empty columns rather than an assumed depth, because a
wrong depth is worse here than none: it would be silently comparable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Iterator

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
    "meta-llama/Llama-3.1-405B": ("llama", 126, 53248),
}

#: Keys that are identifiers or bookkeeping rather than measurements. They
#: become `item_id` or `group`, never a `metric`, so the table is not half full
#: of token ids and case numbers masquerading as readings.
NOT_A_METRIC = {
    "case_id", "position", "base_token", "occurrence", "id", "subject", "qid",
    "hop", "reading", "layer", "n_layers", "d_mlp", "seed",
}


def src_for(ticket: str, model: str, layer: int) -> Source:
    shape = SHAPE.get(model)
    return Source(ticket, model, layer, *shape) if shape else Source(ticket, model, layer)


def numbers(d: dict, skip: set[str] = frozenset()) -> Iterator[tuple[str, float]]:
    """The numeric fields of one record, minus identifiers and anything skipped."""
    for k, v in d.items():
        if k in NOT_A_METRIC or k in skip:
            continue
        if isinstance(v, bool):
            yield k, float(v)
        elif isinstance(v, (int, float)):
            yield k, float(v)


# --------------------------------------------------------------- per-item shapes

def items_list(ticket: str, doc: dict, key: str, *, group_by: str,
               id_by: str) -> list[dict]:
    """A list of per-probe dicts: one row per numeric field of each probe."""
    src = src_for(ticket, doc.get("model", "?"), doc.get("layer", 0))
    out: list[dict] = []
    for it in doc.get(key, []):
        gid = str(it.get(group_by, "all"))
        iid = str(it.get(id_by, len(out)))
        for metric, value in numbers(it):
            out += list(rows(src, gid, metric, [value], [iid]))
    return out


def from_e004(ticket: str, doc: dict) -> list[dict]:
    """Four parallel lists of per-question readings under one key."""
    src = src_for(ticket, doc["model"], doc["layer"])
    out: list[dict] = []
    for metric, values in (doc.get("per_question") or {}).items():
        out += list(rows(src, "hop2", metric, values))
    return out


def from_conformance(ticket: str, doc: dict) -> list[dict]:
    """Named checks, each with an observed value and sometimes a documented one."""
    src = src_for(ticket, doc.get("model", "?"), doc.get("layer", 0))
    out: list[dict] = []
    for r in doc.get("results", []):
        name = r.get("name", "?")
        for metric in ("observed", "documented", "seconds", "traces"):
            if isinstance(r.get(metric), (int, float)):
                out += list(rows(src, "conformance", metric, [r[metric]], [name]))
    return out


def from_layer_sweep(ticket: str, doc: dict) -> list[dict]:
    """The same checks at several layers. The layer varies WITHIN the file.

    This is the only backfilled shape where depth is a variable rather than a
    constant, so each row takes its own layer and gets its own depth fraction.
    """
    model = doc.get("model", "?")
    out: list[dict] = []
    for layer_s, checks in (doc.get("by_layer") or {}).items():
        src = src_for(ticket, model, int(layer_s))
        for r in checks:
            name = r.get("name", "?")
            for metric in ("observed", "documented", "seconds", "traces"):
                if isinstance(r.get(metric), (int, float)):
                    out += list(rows(src, "conformance", metric, [r[metric]], [name]))
    return out


def from_e006(ticket: str, doc: dict) -> list[dict]:
    """One row per reading through a fresh connection; the GPU is the group."""
    src = src_for(ticket, doc.get("model", "?"), doc.get("layer", 0))
    out: list[dict] = []
    for r in doc.get("rows", []):
        gid = f"gpu-{r.get('gpu', '?')}"
        iid = str(r.get("reading", len(out)))
        for metric, value in numbers(r):
            out += list(rows(src, gid, metric, [value], [iid]))
    return out


def from_e040(ticket: str, doc: dict) -> list[dict]:
    """One dict per model, already at the right granularity."""
    out: list[dict] = []
    for r in doc.get("rows", []):
        src = Source(ticket, r["model"], r["layer"], r.get("arch"),
                     r.get("n_layers"), r.get("d_mlp"))
        for metric, value in numbers(r, skip={"depth_fraction_requested",
                                              "depth_fraction_actual", "runtime"}):
            group = "anchor" if metric.startswith("anchor") else "floor"
            out += list(rows(src, group, metric, [value], ["summary"]))
    return out


def from_e039(ticket: str, doc: dict) -> list[dict]:
    """A census of readings recovered from committed logs, grouped by session."""
    src = src_for(ticket, doc.get("model", "?"), doc.get("layer", 0))
    out: list[dict] = []
    for session, body in (doc.get("sessions") or {}).items():
        for r in body.get("rows", []):
            iid = str(r.get("reading", len(out)))
            for metric, value in numbers(r):
                out += list(rows(src, session, metric, [value], [iid]))
    return out


# ------------------------------------------------------------- the scalar sweep

def scalars(ticket: str, doc: dict, claimed: set[str]) -> list[dict]:
    """Every remaining number at any depth, keyed by its dotted path.

    `claimed` names the top-level keys a per-item converter already took, so a
    distribution is not also recorded as whatever summary statistic sits beside
    it. Lists of numbers are walked by index; lists of dicts are left alone,
    since those are what the converters above are for.
    """
    src = src_for(ticket, doc.get("model", "?"), doc.get("layer", 0))
    out: list[dict] = []

    def walk(o: object, path: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if not path and k in claimed:
                    continue
                walk(v, f"{path}{k}.")
        elif isinstance(o, list):
            if o and isinstance(o[0], dict):
                return
            for i, v in enumerate(o):
                walk(v, f"{path}{i}.")
        elif isinstance(o, bool):
            out.extend(rows(src, "summary", path[:-1], [float(o)], ["(flag)"]))
        elif isinstance(o, (int, float)):
            out.extend(rows(src, "summary", path[:-1], [float(o)], ["(scalar)"]))

    walk(doc, "")
    return out


#: glob -> (converter, the top-level keys it consumed)
CONVERTERS: dict[str, tuple[Callable[[str, dict], list[dict]], set[str]]] = {
    "E-001-*.json": (lambda t, d: items_list(t, d, "items", group_by="family",
                                             id_by="id"), {"items"}),
    "E-002-*.json": (lambda t, d: items_list(t, d, "items", group_by="family",
                                             id_by="id"), {"items"}),
    "E-003-*.json": (lambda t, d: items_list(t, d, "items", group_by="family",
                                             id_by="id"), {"items"}),
    "E-004-*.json": (from_e004, {"per_question"}),
    "E-006-*.json": (from_e006, {"rows"}),
    "E-007-*.json": (from_conformance, {"results"}),
    "E-010-*.json": (from_layer_sweep, {"by_layer", "layers"}),
    "E-011-*.json": (from_layer_sweep, {"by_layer", "layers"}),
    "E-015-*.json": (lambda t, d: items_list(t, d, "items", group_by="regime",
                                             id_by="key"), {"items"}),
    "E-016-*.json": (lambda t, d: items_list(t, d, "subjects", group_by="qid",
                                             id_by="subject"), {"subjects"}),
    "E-039-*.json": (from_e039, {"sessions"}),
    "E-040-*.json": (from_e040, {"rows"}),
}

#: Not a result of this project: a catalogue of what the provider serves.
SKIP = {"ndif-catalogue.json"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    seen: set[Path] = set()
    total = 0
    print(f"{'file':<46} {'items':>7} {'scalars':>8}  models")
    print("-" * 86)
    for pattern, (fn, claimed) in CONVERTERS.items():
        for path in sorted(RES.glob(pattern)):
            if path.name in SKIP:
                continue
            seen.add(path)
            doc = json.loads(path.read_text())
            ticket = doc.get("ticket") or path.stem.split("-")[0] + "-" + path.stem.split("-")[1]
            recs = fn(ticket, doc)
            scal = scalars(ticket, doc, claimed)
            dest = a.out / (path.stem + ".csv")
            n = write(dest, recs + scal)
            models = sorted({r["model"] for r in recs + scal})
            print(f"{path.name:<46} {len(recs):>7} {len(scal):>8}  "
                  f"{', '.join(m.split('/')[-1] for m in models)}")
            total += n

    # Anything with no converter still gets its scalars, so nothing is dropped
    # merely for having no array in it.
    for path in sorted(RES.glob("*.json")):
        if path in seen or path.name in SKIP:
            continue
        doc = json.loads(path.read_text())
        ticket = doc.get("ticket", path.stem)
        scal = scalars(ticket, doc, set())
        n = write(a.out / (path.stem + ".csv"), scal)
        print(f"{path.name:<46} {0:>7} {len(scal):>8}  (scalars only)")
        total += n

    # A file that never recorded its model cannot be compared with any other,
    # and the tidy table makes that visible instead of letting a blank column
    # pass for a formatting quirk. Not filled in by inference: E-016's readings
    # are per-subject medians of a model-dependent quantity, so guessing which
    # model would make them look comparable when they are not.
    from collections import defaultdict

    from editreach.tidy import combine
    by_ticket: dict[str, list[str | None]] = defaultdict(list)
    for r in combine(a.out):
        by_ticket[r["ticket"]].append(r["model"])
    # Only a ticket where NOTHING carries a model. A multi-model run's
    # file-level scalars have no single model by construction, and flagging
    # those would bury the real cases under a false one.
    unmodelled = sorted(t for t, ms in by_ticket.items()
                        if all(m in (None, "?") for m in ms))
    if unmodelled:
        print()
        print("NO MODEL RECORDED ANYWHERE, so nothing here is comparable across models:")
        for t in unmodelled:
            print(f"  {t}")

    print(f"\n{total} rows under {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
