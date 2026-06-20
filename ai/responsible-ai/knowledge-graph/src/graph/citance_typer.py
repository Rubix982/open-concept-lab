"""E-011: type intra-corpus citation edges from their citances (Claude).

Reads data/processed/intra_corpus_citations.jsonl (from s2_citations.py). For each edge
that has a citance, classifies the relation the CITING paper has toward the CITED paper
(direction: citing → cited) into our 7-label taxonomy, using the citance as evidence and
the Semantic Scholar intent (background/methodology/result) as a weak prior. Writes
data/processed/cited_edges_typed.jsonl. Edges without a citance are passed through with
relation=null for E-012 to route to the semantic typer.

    python -m src.graph.citance_typer

Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anthropic

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_IN = _PROC / "intra_corpus_citations.jsonl"
_OUT = _PROC / "cited_edges_typed.jsonl"

# Bulk default: haiku (categorizing short citances is well within a small model; ~5x
# cheaper than opus). Reserve opus for evals / quality-ceiling runs via --model.
MODEL = "claude-haiku-4-5"
RELATIONS = [
    "USES", "REFINES", "SUPPORTS", "CONTRADICTS",
    "ADDRESSES_SAME_PROBLEM", "RELATED", "NONE",
]

# Faceted sub-classification (a filterable second layer UNDER the umbrella relation —
# does not replace it). Most useful for decomposing RELATED.
# Per-umbrella facets (R-009): each umbrella carries its own filterable sub-vocabulary.
# RELATED facets answer "what kind of mention?"; USES/REFINES facets answer "a use of what?".
_RELATED_FACETS = [
    "EXEMPLIFIES",   # cited as an instance of a category (esp. surveys: "approaches like [X]")
    "COMPARES",      # positioned against / contrasted, without contradicting
    "BACKGROUND",    # foundational concept / origin attribution
    "MOTIVATION",    # cited to motivate the problem
    "APPLICATION",   # cited as an application domain
    "CRITIQUES",     # flags a weakness/limitation of the cited work (short of CONTRADICTS)
    "FUTURE_WORK",   # cited as an open problem / promising direction
    "RESOURCE",      # points to a dataset / benchmark / tool as available
    "CO_MENTION",    # merely co-listed, no specific function (true residual)
]
_USES_FACETS = [
    "USES_METHOD",        # a technique / algorithm / procedure (incl. loss, regularization)
    "USES_ARCHITECTURE",  # a named model / network (GraphSAGE, Transformer)
    "USES_DATASET",       # a dataset / benchmark
    "USES_METRIC",        # an evaluation metric / protocol
    "USES_TOOL",          # software / optimizer / framework (Adam, PyTorch Geometric)
    "USES_THEORY",        # a theoretical result / foundation (WL test, expressiveness)
]
FACETS = _RELATED_FACETS + _USES_FACETS + ["NA", "OTHER"]

_SYSTEM = (
    "You classify how a CITING paper relates to a paper it CITES, judged from the citance(s) "
    "(sentences in the citing paper containing the citation). If several are given, judge "
    "from the one showing the STRONGEST relation (a substantive 'we use/extend…' outweighs a "
    "background list-mention). Direction is always citing → cited. Choose exactly one "
    "relation:\n"
    "- USES: the citing paper uses a method, dataset, or result from the cited paper.\n"
    "- REFINES: the citing paper improves, generalizes, or extends the cited work.\n"
    "- SUPPORTS: the citing paper's evidence/result corroborates the cited paper's claim.\n"
    "- CONTRADICTS: the citing paper's finding is incompatible with the cited paper's. Rare "
    "in citances — use only with explicit contrastive language ('unlike', 'in contrast to').\n"
    "- ADDRESSES_SAME_PROBLEM: same problem, different approach, no use/refine relation.\n"
    "- RELATED: the citation is a background/related-work mention with no stronger relation "
    "(e.g. listed among examples).\n"
    "- NONE: the citance shows no meaningful relation.\n"
    "You are given the Semantic Scholar intent as a weak prior: methodology → often "
    "USES/REFINES; background → often RELATED/USES; result → often SUPPORTS/CONTRADICTS. "
    "Trust the citance over the prior.\n\n"
    "Then add a FACET appropriate to the relation you chose (it refines the relation, does "
    "NOT replace it), plus a short facet_detail naming the specific.\n"
    "If relation is RELATED, pick one of:\n"
    "- EXEMPLIFIES: instance/example of a category (surveys: 'approaches like [X]'). "
    "facet_detail = the category.\n"
    "- COMPARES: positioned against/contrasted (no contradiction). facet_detail = what's compared.\n"
    "- BACKGROUND: foundational concept / origin attribution. facet_detail = the concept.\n"
    "- MOTIVATION: cited to motivate the problem. facet_detail = the motivation.\n"
    "- APPLICATION: cited as an application domain. facet_detail = the domain.\n"
    "- CRITIQUES: flags a weakness/limitation (short of contradiction). facet_detail = the weakness.\n"
    "- FUTURE_WORK: open problem / promising direction. facet_detail = the direction.\n"
    "- RESOURCE: points to a dataset/benchmark/tool as available. facet_detail = the resource.\n"
    "- CO_MENTION: merely co-listed, no specific function. facet_detail = ''.\n"
    "If relation is USES or REFINES, pick what KIND of thing is used/extended:\n"
    "- USES_METHOD: a technique/algorithm/procedure (incl. loss, regularization, sampling). "
    "facet_detail = the method.\n"
    "- USES_ARCHITECTURE: a named model/network (e.g. GraphSAGE, Transformer). facet_detail = the model.\n"
    "- USES_DATASET: a dataset/benchmark. facet_detail = the dataset.\n"
    "- USES_METRIC: an evaluation metric/protocol. facet_detail = the metric.\n"
    "- USES_TOOL: software/optimizer/framework (e.g. Adam, PyTorch Geometric). facet_detail = the tool.\n"
    "- USES_THEORY: a theoretical result/foundation (e.g. WL test, expressiveness). facet_detail = the result.\n"
    "Otherwise (SUPPORTS / CONTRADICTS / ADDRESSES_SAME_PROBLEM / NONE): use NA.\n"
    "OTHER: only if nothing in the appropriate set fits — name the sub-kind in facet_detail "
    "(do not default to OTHER out of laziness).\n"
    "Keep facet_detail under ~8 words.\n\n"
    "Give calibrated confidence in [0,1] and a one-sentence rationale grounded in the citance."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "relation": {"type": "string", "enum": RELATIONS},
                    "facet": {"type": "string", "enum": FACETS},
                    "facet_detail": {"type": "string"},
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "index", "relation", "facet", "facet_detail", "confidence", "rationale",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


class CitanceTyper:
    def __init__(self, model: str = MODEL, batch_size: int = 10) -> None:
        self.client = anthropic.Anthropic()
        self.model = model
        self.batch_size = batch_size

    def _type_batch(self, edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lines = []
        for i, e in enumerate(edges):
            # Use up to 4 citances (a work is often cited substantively AND in lists);
            # the typer should judge from the strongest one, not just the first.
            cites = [c[:300] for c in (e["citances"] or [])[:4]]
            citance_block = "\n     - ".join(cites) if cites else ""
            intent = ", ".join(e.get("intents") or []) or "none"
            lines.append(
                f"[{i}] citing='{e['citing_title']}' cited='{e['cited_title']}' "
                f"s2_intent={intent}\n     citances:\n     - {citance_block}"
            )
        prompt = (
            f"Classify the citing→cited relation for each of these {len(edges)} citations. "
            "One result per index.\n\n" + "\n\n".join(lines)
        )
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        )
        text = next(b.text for b in resp.content if b.type == "text")
        by_index = {r["index"]: r for r in json.loads(text)["results"]}
        out = []
        for i in range(len(edges)):
            r = by_index.get(i)
            out.append(
                {"relation": None, "facet": None, "facet_detail": "",
                 "confidence": 0.0, "rationale": ""}
                if r is None
                else {
                    "relation": r["relation"],
                    "facet": r["facet"],
                    "facet_detail": r["facet_detail"],
                    "confidence": float(r["confidence"]),
                    "rationale": r["rationale"],
                }
            )
        return out

    def type_edges(self, edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for i in range(0, len(edges), self.batch_size):
            out.extend(self._type_batch(edges[i : i + self.batch_size]))
        return out


def main() -> None:
    import argparse
    from collections import Counter

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="type only the first N citance edges (sample); writes a *_sample file")
    ap.add_argument("--model", default=MODEL,
                    help=f"Claude model (default {MODEL}; use claude-opus-4-8 for evals)")
    args = ap.parse_args()

    edges = [json.loads(l) for l in _IN.read_text().splitlines() if l.strip()]
    with_c = [e for e in edges if e["citances"]]
    without_c = [e for e in edges if not e["citances"]]
    sample = args.limit is not None
    target = with_c[: args.limit] if sample else with_c
    model_tag = args.model.split("-")[1] if "-" in args.model else args.model
    out_path = _OUT.with_name(f"cited_edges_typed_sample_{model_tag}.jsonl") if sample else _OUT
    print(f"{len(edges)} edges: {len(with_c)} with citances; "
          f"typing {len(target)} with {args.model}{' (SAMPLE)' if sample else ''}")

    typed = CitanceTyper(model=args.model).type_edges(target)
    rows = []
    for e, t in zip(target, typed):
        rows.append({
            "citing": e["citing"], "cited": e["cited"],
            "citing_title": e["citing_title"], "cited_title": e["cited_title"],
            "relation": t["relation"], "facet": t["facet"],
            "facet_detail": t["facet_detail"], "direction": "A_TO_B",  # A=citing
            "confidence": t["confidence"], "rationale": t["rationale"],
            "evidence": "citance", "s2_intents": e.get("intents") or [],
        })
    if not sample:
        for e in without_c:
            rows.append({
                "citing": e["citing"], "cited": e["cited"],
                "citing_title": e["citing_title"], "cited_title": e["cited_title"],
                "relation": None, "facet": None, "facet_detail": "", "direction": "A_TO_B",
                "confidence": 0.0, "rationale": "", "evidence": "needs_semantic",
                "s2_intents": e.get("intents") or [],
            })
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    typed_rows = [r for r in rows if r["relation"]]
    na = [r for r in typed_rows if r["facet"] == "NA"]
    print(f"\n=== typed {len(typed)} cited edges ===")
    print("umbrella:", dict(Counter(r["relation"] for r in typed_rows)))
    print("RELATED facets:", dict(Counter(r["facet"] for r in typed_rows if r["relation"] == "RELATED")))
    print("USES/REFINES facets:", dict(Counter(r["facet"] for r in typed_rows if r["relation"] in ("USES", "REFINES"))))
    print(f"NA remaining: {len(na)}/{len(typed_rows)} "
          f"({len(na) / max(len(typed_rows), 1):.0%}) — by umbrella {dict(Counter(r['relation'] for r in na))}")
    print(f"wrote {out_path}")
    print("\n--- USES, now faceted (the NA bucket broken into 'a use of what?') ---")
    shown = 0
    for r in typed_rows:
        if r["relation"] in ("USES", "REFINES") and r["facet"] != "NA":
            d = f" [{r['facet_detail']}]" if r["facet_detail"] else ""
            print(f"  {r['relation']}/{r['facet']}{d}: {r['citing_title'][:28]} -> {r['cited_title'][:28]}")
            shown += 1
            if shown >= 14:
                break


if __name__ == "__main__":
    main()
