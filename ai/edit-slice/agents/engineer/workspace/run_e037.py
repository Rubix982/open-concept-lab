"""E-037 · A floor measured on RippleEdits' materials, and the aliasing arm [E-036] skipped.

[E-036] reported 0.966-1.000 for three same-entity criteria and had nothing to compare it
against. Every criterion it measured — Compositionality included — reads the coefficient at
a token that IS the edited subject, because RippleEdits' compositional prompts name the
edited subject verbatim. So the run contained no different-entity reading and no control.
[E-018]'s 0.082 was measured on our probe set in a different prompt register; importing it
here is an assumption.

    Arm A  the permuted floor — every test prompt scored a SECOND time against a
           different entry's k*. Same prompt, same layer, same token index, same
           arithmetic; only the edit changes. Zero extra remote calls: the keys are
           already read inside each entry's trace and need only be persisted.

    Arm B  Subject Aliasing, selected correctly — the alias is extracted from the test
           prompt's own " of X is" tail and subject_last_index is read at THAT string.
           k* is unchanged. [E-036]'s filter required the canonical label to appear in
           the prompt, which is the condition an alias violates.

The claim is carried by the GAP between the own-k* and permuted-k* columns. Neither column
alone says anything. DELIVERY, NOT EFFECT — [E-028d], 2.96x.
"""
from __future__ import annotations

import argparse
import json
import random
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
from ripple_forms import CRIT, PATS, subject_label  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
LAYER = 5
SAME_ENTITY = ("Relation_Specificity", "Logical_Generalization", "Forgetfulness")
ALIAS = "Subject_Aliasing"
FLOOR_OK, FLOOR_BAD, HIGH = 0.30, 0.60, 0.80
ALIAS_GAP, ALIAS_MIN_N = 0.15, 30


def surface_subject(prompt: str) -> str | None:
    """The subject AS WRITTEN IN THIS PROMPT, not the entry's canonical label.

    For every criterion but aliasing these coincide. For aliasing they are the whole
    point: the released prompt carries the alias ("The place of death of Martin Leo Arons
    is") under a different subject_id, so requiring the canonical label — [E-036]'s
    filter — selects against exactly the cases the criterion exists to test.
    """
    for pat in PATS:
        m = re.search(pat, prompt)
        if m and m.group(1) and m.group(1)[0].isupper():
            return m.group(1).strip()
    return None


def usable(entry: dict) -> tuple[str, str, list[tuple[str, str, str, bool]]] | None:
    """(canonical subject, edit prompt, [(criterion, prompt, subject-in-prompt, is_alias)]).

    `subject-in-prompt` is where the coefficient is read; the canonical subject is what k*
    is read at. They differ only for aliasing, and `is_alias` records whether the surface
    form is genuinely different so the two populations are never merged.
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

    tests: list[tuple[str, str, str, bool]] = []
    for c in CRIT:
        for g in entry.get(c) or []:
            for t in g.get("test_queries") or []:
                p = t.get("prompt")
                if not isinstance(p, str) or not p:
                    continue
                if subj in p:
                    tests.append((c, p, subj, False))
                    continue
                # [E-036] stopped here and dropped the prompt. Recover the surface form.
                s = surface_subject(p)
                if s and s in p:
                    tests.append((c, p, s, True))
    return (subj, edit, tests) if tests else None


def pair_up(subjects: list[str], seed: int) -> tuple[list[int], int]:
    """A derangement over entries, rejecting partners that share a token with the subject.

    Confound 2: a permuted k* is only a floor if the partner is a different entity. Two
    entries about "Maria Anna of Bavaria" and "Maria Anna Leopoldine" are not, and they
    exist in this corpus. Rejections are counted and logged, never silently retried away.
    """
    rng = random.Random(seed)
    n = len(subjects)
    toks = [set(s.lower().split()) for s in subjects]
    partner, rejected = [], 0
    for i in range(n):
        order = list(range(n))
        rng.shuffle(order)
        for j in order:
            if j == i:
                continue
            if toks[i] & toks[j]:
                rejected += 1
                continue
            partner.append(j)
            break
        else:
            partner.append(-1)   # no admissible partner; this entry has no floor reading
    return partner, rejected


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="recent")
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1538)
    a = ap.parse_args()

    entries = json.loads((ROOT / "data" / "ripple" / f"{a.subset}.json").read_text())
    picked, skipped = [], 0
    for e in entries:
        u = usable(e)
        if u is None:
            skipped += 1
            continue
        picked.append(u)
        if len(picked) >= a.n:
            break

    partner, rejected = pair_up([s for s, _, _ in picked], a.seed)
    log = setup("run_e037", config={
        "ticket": "E-037", "model": MODEL, "layer": LAYER, "subset": a.subset,
        "seed": a.seed, "entries_used": len(picked), "entries_skipped": skipped,
        "partner_rejections": rejected,
        "measure": "coefficient only — DELIVERY, not effect; no edit is applied",
        "arms": "A permuted-k* floor on their prompts; B aliasing by surface form"})
    log.info("%d usable entries, %d skipped for want of a recoverable subject label",
             len(picked), skipped)
    log.info("%d candidate partners rejected for sharing a token with their own subject",
             rejected)
    if partner.count(-1):
        log.warning("%d entries have no admissible partner and contribute no floor reading",
                    partner.count(-1))

    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    kcache = ROOT / "results" / "cache" / f"E037_keys_{a.subset}_L{LAYER}.pt"
    keys: dict[str, torch.Tensor] = torch.load(kcache) if kcache.exists() else {}
    rows: dict[str, list] = {}

    for n, (subj, edit, tests) in enumerate(picked, 1):
        key = f"{subj}|{len(tests)}"
        prompts = [edit] + [p for _, p, _, _ in tests]
        subs = [subj] + [s for _, _, s, _ in tests]
        try:
            idxs = [subject_last_index(tok, p, s) for p, s in zip(prompts, subs)]
        except ValueError:
            log.debug("%s: a subject string is not locatable in its own prompt; skipped",
                      subj)
            continue
        rows[key] = [(c, p, is_alias, ix)
                     for (c, p, _s, is_alias), ix in zip(tests, idxs[1:])]
        # A cached entry is reusable only if its ROW COUNT matches the selection we just
        # made. [E-033] scored 29 subjects against 9 cached deltas because a partial cache
        # read as complete; the key alone is not evidence of that, since `usable()` can
        # change under it. Disagreement re-reads rather than raising.
        if key in keys and len(keys[key]) == len(prompts):
            continue
        if key in keys:
            log.warning("cache for %s holds %d rows, selection wants %d — re-reading",
                        subj, len(keys[key]), len(prompts))
        ids = [tok(p).input_ids for p in prompts]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)

        def once(b=batch):
            with _quiet_stdout(), m.trace(b, remote=True):
                k = m.model.layers[LAYER].mlp.down_proj.input.half().save()
            with _quiet_stdout():
                return k

        got = retrying(once, what=f"{subj!r}")
        # Persist only the rows we read at — [n_prompts, d_mlp] for every prompt would be
        # ~90MB over 400 entries and nothing downstream reads the other positions.
        keys[key] = torch.stack([got[j, ix] for j, ix in enumerate(idxs)]).half()
        torch.save(keys, kcache)
        if n % 20 == 0 or n == len(picked):
            log.info("  %d/%d entries", n, len(picked))

    report(picked, partner, keys, rows, skipped, rejected, log, a)


def report(picked, partner, keys, rows, skipped, rejected, log, a) -> None:
    own: dict[str, list[float]] = {c: [] for c in CRIT}
    perm: dict[str, list[float]] = {c: [] for c in CRIT}
    alias_true: list[float] = []
    alias_canon: list[float] = []

    order = [f"{s}|{len(t)}" for s, _, t in picked]
    for i, (subj, _, tests) in enumerate(picked):
        key = order[i]
        if key not in keys or key not in rows:
            continue
        if len(keys[key]) != len(rows[key]) + 1:
            log.error("%s: %d cached key rows against %d selected prompts — dropped from "
                      "the report rather than scored against the wrong positions",
                      subj, len(keys[key]), len(rows[key]) + 1)
            continue
        K = keys[key].float()
        kstar = K[0]
        den = float(kstar @ kstar)
        j_part = partner[i]
        pkey = order[j_part] if 0 <= j_part < len(order) else None
        pstar = keys[pkey][0].float() if pkey in keys else None
        pden = float(pstar @ pstar) if pstar is not None else None
        for r, (c, _p, is_alias, _ix) in enumerate(rows[key], start=1):
            v = float((K[r] @ kstar) / den)
            own[c].append(v)
            if c == ALIAS:
                (alias_true if is_alias else alias_canon).append(v)
            if pstar is not None:
                perm[c].append(float((K[r] @ pstar) / pden))

    def iqr(v):
        v = sorted(v)
        if not v:
            return float("nan")
        return v[min(len(v) - 1, int(0.75 * len(v)))] - v[min(len(v) - 1, int(0.25 * len(v)))]

    log.info("")
    log.info("E-037 — RippleEdits' own prompts against their own k*, and against a stranger's")
    log.info("layer %d · %d entries, %d skipped · seed %d · DELIVERY, not effect",
             LAYER, len(picked), skipped, a.seed)
    log.info("")
    log.info("%-24s%7s%10s%8s%12s%8s%10s", "criterion", "n", "own k*", "IQR",
             "permuted k*", "IQR", "gap")
    med_own, med_perm = {}, {}
    for c in CRIT:
        if not own[c]:
            log.info("%-24s%7s   no prompts selected", c, "0")
            continue
        med_own[c] = st.median(own[c])
        p = st.median(perm[c]) if perm[c] else float("nan")
        med_perm[c] = p
        log.info("%-24s%7d%10.3f%8.3f%12.3f%8.3f%10.3f", c, len(own[c]), med_own[c],
                 iqr(own[c]), p, iqr(perm[c]), med_own[c] - p)

    floor = st.median([v for c in CRIT for v in perm[c]]) if any(perm.values()) else None
    same = [med_own[c] for c in SAME_ENTITY if c in med_own]
    log.info("")
    if floor is None:
        log.error("NO FLOOR — no entry had an admissible partner. Arm A did not run.")
    elif floor <= FLOOR_OK and same and all(x >= HIGH for x in same):
        log.info("ARM A · CONTROLLED — the permuted floor is %.3f against same-entity "
                 "%.3f-%.3f. [E-036]'s reading survives with a control behind it, and the "
                 "separation of %.3f is the number that carries it.", floor, min(same),
                 max(same), st.median(same) - floor)
    elif floor >= FLOOR_BAD:
        log.warning("ARM A · NO SEPARATION — the permuted floor is %.3f. RippleEdits' "
                    "prompt forms are similar enough that the coefficient is near-1 for "
                    "almost any pairing. [E-036]'s headline is WITHDRAWN; what remains is "
                    "a fact about this measure's resolution on a templated corpus.", floor)
    else:
        log.info("ARM A · PARTIAL — the permuted floor is %.3f, between the pre-stated "
                 "bands. Report the table; claim no band.", floor)

    log.info("")
    log.info("ARM B · Subject Aliasing, by surface form")
    log.info("  genuinely different string : n=%d  median %s", len(alias_true),
             f"{st.median(alias_true):.3f}" if alias_true else "—")
    log.info("  canonical label in prompt  : n=%d  median %s", len(alias_canon),
             f"{st.median(alias_canon):.3f}" if alias_canon else "—")
    if not alias_true:
        log.warning("ARM B did not run — no aliasing prompt carried a different surface "
                    "form. Report the n and claim nothing.")
    elif len(alias_true) < ALIAS_MIN_N:
        log.warning("ARM B · UNDERPOWERED — n=%d is below the pre-registered %d. The "
                    "median is %.3f and is reported as such; no sentence about what the "
                    "coefficient is keyed on. This threshold was fixed before the run "
                    "because [E-036] drew a conclusion from 8 near-identical strings.",
                    len(alias_true), ALIAS_MIN_N, st.median(alias_true))
    elif same and st.median(alias_true) <= st.median(same) - ALIAS_GAP:
        log.info("ARM B · STRING-KEYED — aliases sit %.3f below the same-entity median "
                 "(%.3f vs %.3f). The coefficient is a property of the surface form, so a "
                 "benchmark that renames its subject is measuring a different key.",
                 st.median(same) - st.median(alias_true), st.median(alias_true),
                 st.median(same))
    else:
        log.info("ARM B · ENTITY-KEYED — aliases sit within %.2f of the same-entity "
                 "median (%.3f vs %.3f) at n=%d. Renaming the subject does not move the "
                 "key.", ALIAS_GAP, st.median(alias_true), st.median(same or [0]),
                 len(alias_true))

    out = ROOT / "results" / "E-037-ripple-floor.json"
    out.write_text(json.dumps({
        "ticket": "E-037", "layer": LAYER, "seed": a.seed, "subset": a.subset,
        "n_entries": len(picked), "skipped": skipped, "partner_rejections": rejected,
        "median_own": med_own, "median_permuted": med_perm, "floor": floor,
        "alias_different_surface": alias_true, "alias_canonical_substring": alias_canon,
        "per_criterion_own": own, "per_criterion_permuted": perm}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
