"""Emit the per-experiment value tables for the paper's appendix.

Appendix B already names the run behind every number. It does not carry the
numbers, so a reader who wants to check a claim has to take the figure on
trust — and the raw outputs under `results/` are gitignored, so there is
nothing for them to open. This puts the values themselves on the page.

Each row names the **field it was read from**, which is the part that pays.
[E-004] reports two different floors for the same probes — a same-relation
stranger at 0.0480 and a different-relation one at 0.0294 — and §5.2 cites the
first. A reader seeing only "+0.0002" cannot tell which; a reader seeing
`hop2.excess_over_same_relation` can.

    python3 ai/edit-reach/tools/appendix_values.py

Writes web/notebook/edit-reach/_values.mdx. A field this script asks for and
does not find is printed as a missing row rather than skipped, because a table
that silently drops what it cannot find is worse than one with a hole in it.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
RES = ROOT / "ai" / "edit-reach" / "results"
OUT = ROOT / "web" / "notebook" / "edit-reach" / "_values.mdx"

#: Per-experiment group tables: every row the run produced, not just its summary.
#: (ticket, dotted path to the dict of groups, group-column label,
#:  [(column label, subpath within each group, format)])
GROUPS: dict[str, tuple[str, str, list[tuple[str, str, str]]]] = {
    "E-001": ("by_family", "probe family", [
        ("n", "n", "d"),
        ("raw ρ", "raw.rho", "f4"),
        ("raw 95% CI", "raw.ci95", "ci"),
        ("excess ρ", "excess.rho", "f4"),
        ("excess 95% CI", "excess.ci95", "ci"),
    ]),
    "E-002": ("by_family", "probe family", [
        ("n", "n", "d"),
        ("real edit", "real", "f4"),
        ("same-subject control", "ctl", "f4"),
        ("different-subject control", "other", "f4"),
    ]),
    "E-003": ("by_family", "probe family", [
        ("n", "n", "d"),
        ("destination, real", "hit_real", "f4"),
        ("destination, same-subj", "hit_ctl", "f4"),
        ("destination, diff-subj", "hit_other", "f4"),
        ("destruction, real", "destruction_real", "f4"),
        ("destruction, same-subj", "destruction_ctl", "f4"),
        ("destruction, diff-subj", "destruction_other", "f4"),
    ]),
}

#: (ticket, file, heading, note, [(label, dotted path, format)])
SPEC: list[tuple[str, str, str, str, list[tuple[str, str, str]]]] = [
    ("E-001", "E-001-predicted-vs-measured.json",
     "Predicted reach against measured movement",
     "The headline of §5.1. The raw correlation is the one that will be quoted; the excess is the one that survives a control.",
     [("probes", "probe_set.items", "d"),
      ("subjects", "probe_set.subjects", "d"),
      ("raw Spearman", "overall.raw.rho", "f4"),
      ("raw 95% CI", "overall.raw.ci95", "ci"),
      ("excess Spearman", "overall.excess.rho", "f4"),
      ("excess 95% CI", "overall.excess.ci95", "ci"),
      ("anchor gate, worst deviation", "anchor_gate.worst_deviation", "f4")]),

    ("E-002", "E-002-different-subject-arm.json",
     "Identity against content",
     "§5.3. Three arms on the same probes: the real edit, a different property of the same person, and another person's edit matched on magnitude.",
     [("probes", "overall.n", "d"),
      ("median movement, real edit", "overall.real", "f4"),
      ("median movement, same-subject control", "overall.ctl", "f4"),
      ("median movement, different-subject control", "overall.other", "f4"),
      ("pairing, median |Δv|/|k*| difference", "pairing.median_abs_diff", "f4")]),

    ("E-003", "E-003-destination.json",
     "Destruction and destination",
     "§5.4, under a full-vocabulary argmax readout rather than a fixed-token one.",
     [("probes", "overall.n", "d"),
      ("destination hit rate, before the edit", "overall.hit_base", "f4"),
      ("destination hit rate, real edit", "overall.hit_real", "f4"),
      ("destination hit rate, same-subject control", "overall.hit_ctl", "f4"),
      ("destination hit rate, different-subject control", "overall.hit_other", "f4"),
      ("destruction, real edit", "overall.destruction_real", "f4"),
      ("destruction, same-subject control", "overall.destruction_ctl", "f4"),
      ("destruction, different-subject control", "overall.destruction_other", "f4")]),

    ("E-004", "E-004-far-field-floor.json",
     "The far field, under two different floors",
     "§5.2. The paper cites the same-relation floor. The other is kept here because the same run produced both, and the difference between them is larger than the effect either one measures.",
     [("hop-2 questions", "hop2.n_questions", "d"),
      ("donors per question", "hop2.donors_per_question", "d"),
      ("median coefficient, own k*", "hop2.own_median", "f4"),
      ("floor, same-relation stranger", "hop2.floor_same_relation", "f4"),
      ("excess over same-relation floor", "hop2.excess_over_same_relation", "f4"),
      ("floor, different-relation stranger", "hop2.floor_diff_relation", "f4"),
      ("excess over different-relation floor", "hop2.excess_over_diff_relation", "f4")]),

    ("E-015", "E-015-bound-looseness.json",
     "Looseness of the upper bound, by regime",
     "§5.6. Looseness is the bound divided by the coefficient actually delivered, so 1.00 would mean the bound is tight.",
     [("near-field questions", "summary.near.n", "d"),
      ("near-field median looseness", "summary.near.median_looseness", "f4"),
      ("near-field 95% CI", "summary.near.ci95", "ci"),
      ("near-field median coefficient", "summary.near.median_c", "f4"),
      ("far-field questions", "summary.far.n", "d"),
      ("far-field median looseness", "summary.far.median_looseness", "f4"),
      ("far-field 95% CI", "summary.far.ci95", "ci"),
      ("far-field median coefficient", "summary.far.median_c", "f4"),
      ("far-field median bound", "summary.far.median_bound", "f4")]),

    ("E-016", "E-016-subject-properties.json",
     "Subject properties against damage",
     "§5.7. Six relationships were computed and all six are here, so reporting a subset would have been a choice.",
     [("subjects", "n_subjects", "d"),
      ("prominence vs damage", "results.prominence vs damage.rho", "f4"),
      ("prominence 95% CI", "results.prominence vs damage.ci95", "ci"),
      ("dependent count vs damage", "results.dependent count vs damage.rho", "f4"),
      ("dependent count 95% CI", "results.dependent count vs damage.ci95", "ci"),
      ("total statements vs damage", "results.total statements vs damage.rho", "f4"),
      ("headroom vs damage", "results.headroom (p_base) vs damage.rho", "f4"),
      ("prominence vs dependent count", "predictor_correlation_prominence_vs_dependent", "f4")]),
    ("E-005", "E-005-loader-parity.json",
     "Whether the two nnsight loaders are the same instrument",
     "§4.1. Three repeats per loader, so a reading can be compared against another reading of itself before it is compared across loaders.",
     [("repeats per loader", "repeats_per_loader", "d"),
      ("same module structure", "same_structure", "raw"),
      ("worst |difference|, within LanguageModel", "within_loader.language.worst_abs", "f4"),
      ("worst |difference|, within TransformersModel", "within_loader.transformers.worst_abs", "f4"),
      ("worst |difference|, between loaders", "between_loaders.worst_abs", "f4"),
      ("difference attributable to the loader", "difference_attributable_to_loader", "raw"),
      ("published floor it was checked against", "e001_floor_median", "f4")]),

    ("E-006", "E-006-session-variation.json",
     "Whether a remote reading repeats across sessions",
     "§4.1. Sixteen readings of the same 84 prompts, byte-identical inputs, taken across serving sessions.",
     [("readings", "readings", "d"),
      ("prompts per reading", "n_prompts", "d"),
      ("distinct values seen", "distinct_values", "d"),
      ("distinct GPUs seen", "distinct_gpus", "d"),
      ("values partition by GPU", "partitions_by_gpu", "raw"),
      ("anchor gate, worst deviation", "anchor_worst_deviation_overall", "f4"),
      ("floor spread within one GPU", "floor_spread_within_gpu", "f4"),
      ("floor spread across GPUs", "floor_spread_across_gpus", "f6")]),

    ("E-039", "E-039-log-census.json",
     "What the committed logs kept that the result files overwrote",
     "§4.1. A runner writes one JSON per ticket, so a second run overwrites the first. These are the readings both logs kept.",
     [("sessions with device readings", "sessions_with_device_readings", "d"),
      ("readings", "readings", "d"),
      ("distinct values", "distinct_signatures", "d"),
      ("one value per device within a session", "one_value_per_device_within_a_session", "raw"),
      ("one value per device across sessions", "one_value_per_device_across_sessions", "raw")]),

    ("E-007", "E-007-shape.json",
     "Batch reshaping against raw key magnitude, re-run",
     "§4.1. Re-run on 15 November 2026 to restore a row whose original output was lost. The claim it backs — that reshaping moves the raw keys by about 2.6% of their magnitude while leaving the derived ratio alone — was made from the run of 2 November.",
     [("difference in the derived ratio", "by_layer.5.0.observed", "f6"),
      ("difference in the raw keys", "by_layer.5.0.extra.raw_key_difference", "f6"),
      ("key magnitude", "by_layer.5.0.extra.key_magnitude", "f6"),
      ("raw difference as a fraction of magnitude", "by_layer.5.0.extra.raw_relative", "f6"),
      ("raw keys bit-identical", "by_layer.5.0.extra.raw_bit_identical", "raw"),
      ("pad-width only, max |difference|", "by_layer.5.1.observed", "f6"),
      ("rows touched by pad width alone", "by_layer.5.1.extra.rows_touched", "raw")]),
]



def dig(doc: object, path: str) -> object | None:
    """Walk a dotted path. A numeric step indexes a list, because a run that
    reports its checks as an ordered list is still a path a spec should be able
    to name."""
    for key in path.split("."):
        if isinstance(doc, dict) and key in doc:
            doc = doc[key]
        elif isinstance(doc, list) and key.isdigit() and int(key) < len(doc):
            doc = doc[int(key)]
        else:
            return None
    return doc


def render(value: object, kind: str) -> str:
    if value is None:
        return "—"
    if kind == "d":
        return f"{int(value):,}"
    if kind == "raw":
        return "yes" if value is True else "no" if value is False else str(value)
    if kind == "f6":
        return f"{float(value):.6f}"
    if kind == "ci" and isinstance(value, list) and len(value) == 2:
        return f"{value[0]:+.4f} to {value[1]:+.4f}"
    if isinstance(value, (int, float)):
        return f"{float(value):+.4f}"
    return str(value)


def main() -> None:
    L = ["{/* Generated by ai/edit-reach/tools/appendix_values.py. Do not edit. */}", ""]
    L.append("Every number the results sections rest on, as the run wrote it, with the "
             "field it was read from. The raw outputs under `results/` are not in the "
             "repository, so these tables are the only place a reader can check a figure "
             "against its source.")
    L.append("")
    missing = 0
    for ticket, fname, heading, note, fields in SPEC:
        path = RES / fname
        L.append(f"**{ticket} · {heading}**")
        L.append("")
        if not path.is_file():
            L.append(f"`{fname}` is not on this machine, so this table could not be built.")
            L.append("")
            missing += len(fields)
            continue
        doc = json.loads(path.read_text())
        L.append(note)
        L.append("")
        # <Data> rather than a markdown table. Paper mode sets two columns on
        # the article and only .ocl-ptable spans both, so a plain table was
        # being squeezed into one column and hyphenated to pieces —
        # "destina-tion", "discrimi-nation". This is the component the paper's
        # own tables use, so these look like the rest of them.
        L.append(f"<Data caption={{<>Every quantity {ticket} produced that the paper "
                 f"cites, with the field it was read from in <code>{fname}</code>.</>}}>")
        L.append("  <thead>")
        L.append('    <tr><th>quantity</th><th className="n">value</th><th>field</th></tr>')
        L.append("  </thead>")
        L.append("  <tbody>")
        for label, dotted, kind in fields:
            value = dig(doc, dotted)
            if value is None:
                missing += 1
            L.append(f'    <tr><td>{label}</td><td className="n">{render(value, kind)}</td>'
                     f'<td><code>{dotted}</code></td></tr>')
        L.append("  </tbody>")
        L.append("</Data>")
        L.append("")

        # Every group the run produced, not a selection of them. A summary row
        # hides which probe families carry the effect and which do not, and the
        # families differ enough here that the overall figure is an average over
        # things that behave differently.
        if ticket in GROUPS:
            gpath, gcol, cols = GROUPS[ticket]
            groups = dig(doc, gpath)
            if not isinstance(groups, dict):
                L.append(f"`{gpath}` is missing from this run, so the breakdown is not here.")
                L.append("")
                missing += 1
            else:
                L.append(f"<Data caption={{<>Every group in <code>{gpath}</code>, "
                         f"as the run wrote it.</>}}>")
                L.append("  <thead>")
                heads = "".join(f'<th className="n">{c[0]}</th>' for c in cols)
                L.append(f"    <tr><th>{gcol}</th>{heads}</tr>")
                L.append("  </thead>")
                L.append("  <tbody>")
                for name in sorted(groups):
                    cells = "".join(
                        f'<td className="n">{render(dig(groups[name], sub), kind)}</td>'
                        for _, sub, kind in cols)
                    L.append(f"    <tr><td>{name}</td>{cells}</tr>")
                L.append("  </tbody>")
                L.append("</Data>")
                L.append("")
    L.append("**What is not in these tables.** [E-007] and [E-009] are conformance "
             "sweeps whose grid is drawn in §4.1 rather than tabulated here. [E-038], the "
             "RippleEdits re-run over 23,505 readings, wrote to a run directory that is "
             "not on this machine, so its figures appear in §5.5 from the summary and "
             "cannot be reprinted from their source. Saying so is the point of this "
             "paragraph: an appendix that lists only what it happens to have is not a "
             "record of what was run.")
    L.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(SPEC)} experiments, {missing} value(s) not found")


if __name__ == "__main__":
    main()
