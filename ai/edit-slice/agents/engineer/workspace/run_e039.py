"""E-039 · MQuAKE hop-1 against hop-2+ — the within-benchmark control. [T-088, R-014]

[E-037] measured 0.982 on RippleEdits' different-entity tests, and the reason was that
their prompts name the edited subject verbatim. Its control was a PERMUTED k*, which is
synthetic: it answers "would a stranger's edit reach this prompt", not "does a real
different-entity test escape its own edit".

[R-014] found a benchmark that supplies the second control without anyone constructing it.
MQuAKE names the edited subject in a multi-hop question **iff the edit is on hop 1** —
6,861 of 6,861, and 0 of 16,506 — because it phrases a chain from its head, so a hop-2 edit
targets an entity the question never mentions:

    chain      Michael Feinstein -> citizenship -> UNITED STATES OF AMERICA -> capital -> DC
    edit       hop 2, subject "United States of America"
    question   "What is the capital city of the country that Michael Feinstein is a
                citizen of?"

Both arms therefore sit in one dataset, one prompt register, one edit set — differing in
the single property under test, and the split is read off the benchmark's own metadata.

THE POSITION PROBLEM. A hop-2+ question has no subject token to read. Three choices were
available; the ticket pre-registered two and dropped one:

    arm FINAL   final token of the prompt, BOTH arms. The headline: the only reading where
                a hop difference cannot be an artifact of reading different positions.
    arm NATURAL subject position where one exists, final token where it does not. What a
                practitioner actually gets.
    (dropped)   final token for hop-2+ and subject for hop-1 — incomparable by construction.

DELIVERY, NOT EFFECT. [E-028d], 2.96x. Nothing here measures how far an answer moves.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from mquake_forms import hop_of  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
LAYER = 5
ESCAPES_HI, ESCAPES_LO = 0.70, 0.30


def usable(entry: dict) -> dict | None:
    """One single-edit instance, with the hop its edit sits on and its questions.

    Single-edit only: a multi-edit instance has no unambiguous "which hop was edited", and
    attributing it to one would be the kind of quiet choice [E-036] shipped.
    """
    rw = entry.get("requested_rewrite") or []
    if len(rw) != 1:
        return None
    r = rw[0]
    subj, tmpl = r.get("subject"), r.get("prompt")
    if not subj or not tmpl or "{}" not in tmpl:
        return None
    hop = hop_of(entry, subj)
    chain = entry.get("orig", {}).get("triples_labeled") or []
    qs = [q for q in (entry.get("questions") or []) if isinstance(q, str) and q]
    if hop is None or not chain or not qs:
        return None
    return {"case_id": entry.get("case_id"), "subject": subj,
            "edit": tmpl.format(subj).rstrip(".").strip(), "hop": hop,
            "chain_len": len(chain), "relation": r.get("relation_id"), "questions": qs}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", default="MQuAKE-CF-3k.json")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--chain-len", type=int, default=0,
                    help="0 = every chain length; 2 = the controlled comparison only")
    a = ap.parse_args()

    entries = json.loads((ROOT / "data" / "mquake" / a.file).read_text())
    picked, skipped = [], 0
    for e in entries:
        u = usable(e)
        if u is None:
            skipped += 1
            continue
        if a.chain_len and u["chain_len"] != a.chain_len:
            continue
        picked.append(u)
        if len(picked) >= a.n:
            break

    log = setup("run_e039", config={
        "ticket": "E-039", "model": MODEL, "layer": LAYER, "file": a.file,
        "instances": len(picked), "skipped": skipped, "chain_len_filter": a.chain_len,
        "arms": "FINAL (headline, both arms at the final token); NATURAL (subject where present)",
        "measure": "coefficient only — DELIVERY, not effect; no edit is applied"})
    log.info("%d single-edit instances, %d skipped (multi-edit or unlocatable hop)",
             len(picked), skipped)
    hops = {}
    for u in picked:
        hops[u["hop"]] = hops.get(u["hop"], 0) + 1
    log.info("by hop carrying the edit: %s", dict(sorted(hops.items())))

    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    cache = ROOT / "results" / "cache" / f"E039_{a.file}_L{LAYER}_c{a.chain_len}.json"
    done = json.loads(cache.read_text()) if cache.exists() else {}

    for n, u in enumerate(picked, 1):
        key = f"{u['case_id']}|{len(u['questions'])}"
        # The row count must match what this selection wants, or a cache written under a
        # different filter reads as complete. [E-033], and [E-037]'s own near-miss.
        if key in done and len(done[key]["final"]) == len(u["questions"]):
            continue
        prompts = [u["edit"]] + u["questions"]
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

        keys = retrying(once, what=f"case {u['case_id']} hop {u['hop']}")
        try:
            kstar = keys[0, subject_last_index(tok, u["edit"], u["subject"])]
        except ValueError:
            log.debug("case %s: subject not locatable in its own edit prompt", u["case_id"])
            continue
        den = float(kstar @ kstar)

        final, natural, named = [], [], []
        for j, q in enumerate(u["questions"], start=1):
            last = len(ids[j]) - 1
            final.append(float((keys[j, last] @ kstar) / den))
            if u["subject"] in q:
                named.append(True)
                natural.append(float(
                    (keys[j, subject_last_index(tok, q, u["subject"])] @ kstar) / den))
            else:
                named.append(False)
                natural.append(final[-1])
        done[key] = {"hop": u["hop"], "chain_len": u["chain_len"],
                     "relation": u["relation"], "final": final, "natural": natural,
                     "names_subject": named}
        cache.write_text(json.dumps(done))
        if n % 20 == 0 or n == len(picked):
            log.info("  %d/%d instances", n, len(picked))

    report(done, skipped, log, a)


def report(done: dict, skipped: int, log, a) -> None:
    rows = list(done.values())

    def med(vals):
        return st.median(vals) if vals else float("nan")

    def iqr(v):
        v = sorted(v)
        if not v:
            return float("nan")
        return v[min(len(v) - 1, int(.75 * len(v)))] - v[min(len(v) - 1, int(.25 * len(v)))]

    def pull(pred, arm):
        return [x for r in rows if pred(r) for x in r[arm]]

    log.info("")
    log.info("E-039 — MQuAKE, hop-1 against hop-2+, at layer %d. DELIVERY, not effect.", LAYER)
    log.info("%d instances, %d skipped", len(rows), skipped)
    log.info("")
    log.info("%-22s%8s%10s%8s%12s%8s", "arm", "n", "FINAL", "IQR", "NATURAL", "IQR")
    for label, pred in (("hop 1 (names subj)", lambda r: r["hop"] == 1),
                        ("hop 2+ (does not)", lambda r: r["hop"] >= 2)):
        f, nat = pull(pred, "final"), pull(pred, "natural")
        log.info("%-22s%8d%10.3f%8.3f%12.3f%8.3f", label, len(f), med(f), iqr(f),
                 med(nat), iqr(nat))

    # Confound 1 — question form varies with chain length. The 2-hop row holds it.
    log.info("")
    log.info("CONTROLLED — 2-hop chains only, where both arms' questions have the same shape")
    log.info("%-22s%8s%10s%8s", "arm", "n", "FINAL", "IQR")
    two = {}
    for label, h in (("hop 1", 1), ("hop 2", 2)):
        f = pull(lambda r, h=h: r["hop"] == h and r["chain_len"] == 2, "final")
        two[h] = med(f)
        log.info("%-22s%8d%10.3f%8.3f", label, len(f), med(f), iqr(f))

    # Confound 3 — the arms' relation mixes differ. P495 appears in BOTH, so it gives a
    # relation-matched sub-comparison the ticket did not anticipate. Reported whenever
    # both sides have any, with the n stated rather than a threshold assumed.
    shared = sorted({r["relation"] for r in rows if r["hop"] == 1}
                    & {r["relation"] for r in rows if r["hop"] >= 2})
    if shared:
        log.info("")
        log.info("RELATION-MATCHED — relations appearing in BOTH arms (confound 3)")
        log.info("%-12s%10s%10s%10s%10s", "relation", "n hop1", "hop1", "n hop2+", "hop2+")
        for rel in shared[:8]:
            f1 = pull(lambda r, x=rel: r["hop"] == 1 and r["relation"] == x, "final")
            f2 = pull(lambda r, x=rel: r["hop"] >= 2 and r["relation"] == x, "final")
            log.info("%-12s%10d%10s%10d%10s", rel, len(f1),
                     f"{med(f1):.3f}" if f1 else "—", len(f2),
                     f"{med(f2):.3f}" if f2 else "—")
    else:
        log.warning("no relation appears in both arms — confound 3 is UNCONTROLLED and "
                    "any hop difference may be a relation difference instead")

    h1 = med(pull(lambda r: r["hop"] == 1, "final"))
    h2 = med(pull(lambda r: r["hop"] >= 2, "final"))
    log.info("")
    if h2 != h2 or h1 != h1:
        log.error("one arm is empty — nothing to compare")
    elif h2 <= ESCAPES_LO and h1 >= ESCAPES_HI:
        log.info("VERDICT: ESCAPES — hop-2+ questions sit at %.3f against hop-1's %.3f. A "
                 "genuine different-entity test does escape the update, and [E-037]'s "
                 "0.982 is a property of RippleEdits' CONSTRUCTION rather than of "
                 "multi-hop testing. §4.6 must say so.", h2, h1)
    elif h2 >= ESCAPES_HI:
        log.warning("VERDICT: NO ESCAPE — hop-2+ sits at %.3f. Naming the subject is NOT "
                    "what delivers the update, [E-037]'s explanation of Table 11 is wrong, "
                    "and the §4.6 reading needs rewriting. [E-019] measured 0.95 for "
                    "subject-late probes, so this was live.", h2)
    else:
        log.info("VERDICT: BETWEEN — hop-1 %.3f, hop-2+ %.3f, gap %.3f. Report both; "
                 "claim no band.", h1, h2, h1 - h2)

    out = ROOT / "results" / f"E-039-mquake-hops-{a.file.replace('.json', '')}.json"
    out.write_text(json.dumps({"ticket": "E-039", "layer": LAYER, "file": a.file,
                               "chain_len_filter": a.chain_len, "skipped": skipped,
                               "median_final_hop1": h1, "median_final_hop2plus": h2,
                               "two_hop": two, "rows": rows}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
