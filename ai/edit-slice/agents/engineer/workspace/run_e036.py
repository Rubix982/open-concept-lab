"""E-036 · How much of a ROME update reaches RippleEdits' own test prompts? [R-013, T-003]

[R-013] killed the priced week by killing its premise — RippleEdits is already
subject-final, so there is nothing to rewrite. This is what replaces it: take THEIR edits
and THEIR test prompts and measure what fraction of the update each would receive.

    k*          read at the subject's last token of the entry's own edit prompt
    coefficient (k·k*)/(k*·k*) at the subject's last token of each test prompt
    layer       5 — what EasyEdit's llama3-8b.yaml edits

**Their taxonomy is the control structure, and none of it was designed by us:**

    Relation Specificity   same entity, different relation      -> high
    Logical Generalization same entity, inverse/symmetric       -> high
    Forgetfulness          same entity, negated relation        -> high
    Subject Aliasing       SAME entity, DIFFERENT STRING        -> lower, if the key is
                                                                   a property of the string
    Compositionality I/II  a DIFFERENT entity, one hop away     -> at [E-018]'s 0.082 floor

Subject Aliasing is the measurement that matters most and the one we are least sure of. A
drop says the coefficient is keyed on the string; no drop says it is keyed on the entity.
We predict a drop. A non-drop would be the more interesting result and must be reported as
plainly as the headline.

DELIVERY, NOT EFFECT. [E-028d] showed these come apart by 2.96x. Nothing here measures how
far an answer moves.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402
from ripple_forms import CRIT, subject_label  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
LAYER = 5
SAME_ENTITY = ("Relation_Specificity", "Logical_Generalization", "Forgetfulness")
DIFFERENT_ENTITY = ("Compositionality_I", "Compositionality_II")
HIGH, FLOOR, UNDIFF = 0.80, 0.30, 0.15


def usable(entry: dict) -> tuple[str, str, list[tuple[str, str]]] | None:
    """(subject, materialised edit prompt, [(criterion, test prompt)]) or None.

    An entry is usable only when a subject label can be recovered from one of its
    materialised prompts — the released data carries the subject as a Wikidata id and
    does not always substitute it. Attrition is reported, never silently dropped.
    """
    subj = subject_label(entry)
    edit = (entry.get("edit") or {}).get("prompt") or ""
    if not subj or not edit:
        return None
    if re.search(r"\s{2,}", edit):
        edit = re.sub(r"\s{2,}", f" {subj} ", edit)
    elif subj not in edit:
        return None
    edit = edit.rstrip(".").strip()
    tests = [(c, t["prompt"]) for c in CRIT for g in (entry.get(c) or [])
             for t in (g.get("test_queries") or [])
             if isinstance(t.get("prompt"), str) and subj in t["prompt"]]
    return (subj, edit, tests) if tests else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="recent")
    ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()

    entries = json.loads((ROOT / "data" / "ripple" /
                          f"{a.subset}.json").read_text())
    picked, skipped = [], 0
    for e in entries:
        u = usable(e)
        if u is None:
            skipped += 1
            continue
        picked.append(u)
        if len(picked) >= a.n:
            break

    log = setup("run_e036", config={
        "ticket": "E-036", "model": MODEL, "layer": LAYER, "subset": a.subset,
        "entries_used": len(picked), "entries_skipped": skipped,
        "measure": "coefficient only — DELIVERY, not effect; no edit is applied",
        "k_star": "the entry's own edit prompt, at the subject's last token"})
    log.info("%d usable entries, %d skipped for want of a recoverable subject label",
             len(picked), skipped)

    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    acc: dict[str, list[float]] = {c: [] for c in CRIT}
    cache = ROOT / "results" / "cache" / f"E036_{a.subset}_L{LAYER}.json"
    done = json.loads(cache.read_text()) if cache.exists() else {}

    for n, (subj, edit, tests) in enumerate(picked, 1):
        key = f"{subj}|{len(tests)}"
        if key in done:
            for c, v in done[key]:
                acc[c].append(v)
            continue
        prompts = [edit] + [p for _, p in tests]
        try:
            idxs = [subject_last_index(tok, p, subj) for p in prompts]
        except ValueError:
            continue
        ids = [tok(p).input_ids for p in prompts]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)

        def once(b=batch):
            with _quiet_stdout(), m.trace(b, remote=True):
                k = m.model.layers[LAYER].mlp.down_proj.input.half().save()
            with _quiet_stdout():
                return k.float()

        keys = retrying(once, what=f"{subj!r}")
        kstar = keys[0, idxs[0]]
        den = float(kstar @ kstar)
        row = []
        for j, (c, _) in enumerate(tests, start=1):
            v = float((keys[j, idxs[j]] @ kstar) / den)
            acc[c].append(v)
            row.append((c, v))
        done[key] = row
        cache.write_text(json.dumps(done))
        if n % 20 == 0 or n == len(picked):
            log.info("  %d/%d entries", n, len(picked))

    report(acc, len(picked), skipped, log)


def report(acc: dict[str, list[float]], n_used: int, skipped: int, log) -> None:
    def q(v, p):
        v = sorted(v)
        return v[min(len(v) - 1, int(p * len(v)))] if v else float("nan")

    log.info("")
    log.info("E-036 — fraction of a ROME update reaching RippleEdits' own test prompts")
    log.info("layer %d · %d entries used, %d skipped · DELIVERY, not effect", LAYER,
             n_used, skipped)
    log.info("")
    log.info("%-24s%8s%10s%10s%8s", "criterion", "n", "median", "IQR", "entity")
    med = {}
    for c in CRIT:
        v = acc[c]
        if not v:
            log.info("%-24s%8s", c, "—")
            continue
        med[c] = st.median(v)
        kind = "same" if c in SAME_ENTITY else ("diff" if c in DIFFERENT_ENTITY else "alias")
        log.info("%-24s%8d%10.3f%10.3f%8s", c, len(v), med[c],
                 q(v, 0.75) - q(v, 0.25), kind)

    same = [med[c] for c in SAME_ENTITY if c in med]
    diff = [med[c] for c in DIFFERENT_ENTITY if c in med]
    alias = med.get("Subject_Aliasing")
    log.info("")
    if alias is not None and same:
        log.info("Subject Aliasing %.3f against same-entity median %.3f — the coefficient "
                 "is keyed on the %s", alias, st.median(same),
                 "STRING" if alias < st.median(same) - 0.15 else "ENTITY, not the string")

    spread = (max(med.values()) - min(med.values())) if med else 0.0
    if spread < UNDIFF:
        log.warning("VERDICT: UNDIFFERENTIATED — every criterion within %.2f of every "
                    "other. The coefficient does not distinguish their test types and "
                    "this measurement says nothing about them.", spread)
    elif same and all(x >= HIGH for x in same) and diff and all(x <= FLOOR for x in diff):
        log.info("VERDICT: MECHANICAL — their same-entity tests (%.2f-%.2f) receive most "
                 "of the update by arithmetic while their different-entity tests "
                 "(%.2f-%.2f) do not. Reportable against their own taxonomy, and it is "
                 "about DELIVERY only.", min(same), max(same), min(diff), max(diff))
    elif same and all(x < 0.50 for x in same):
        log.warning("VERDICT: NOT MECHANICAL — same-entity tests sit below 0.50 (%.2f-%.2f)."
                    " The concern does not apply to this benchmark and §7 item 2 should be "
                    "withdrawn entirely. This is the most useful outcome available: it "
                    "closes the project's one outward-facing claim honestly.",
                    min(same), max(same))
    else:
        log.info("VERDICT: between the pre-stated bands (same-entity %.2f-%.2f, "
                 "different-entity %.2f-%.2f). Report the table, claim neither.",
                 min(same or [0]), max(same or [0]), min(diff or [0]), max(diff or [0]))

    out = ROOT / "results" / "E-036-ripple-coefficients.json"
    out.write_text(json.dumps({"ticket": "E-036", "layer": LAYER, "n_entries": n_used,
                               "skipped": skipped,
                               "median": med, "per_criterion": acc}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
