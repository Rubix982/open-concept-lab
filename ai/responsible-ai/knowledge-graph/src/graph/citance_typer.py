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

MODEL = "claude-opus-4-8"
RELATIONS = [
    "USES", "REFINES", "SUPPORTS", "CONTRADICTS",
    "ADDRESSES_SAME_PROBLEM", "RELATED", "NONE",
]

# Faceted sub-classification (a filterable second layer UNDER the umbrella relation —
# does not replace it). Most useful for decomposing RELATED.
FACETS = [
    "EXEMPLIFIES",   # cited as an instance of a category (esp. surveys: "approaches like [X]")
    "COMPARES",      # positioned against / contrasted, without contradicting
    "BACKGROUND",    # foundational concept / origin attribution
    "MOTIVATION",    # cited to motivate the problem
    "APPLICATION",   # cited as an application domain
    "CRITIQUES",     # flags a weakness/limitation of the cited work (short of CONTRADICTS)
    "FUTURE_WORK",   # cited as an open problem / promising direction
    "RESOURCE",      # points to a dataset / benchmark / tool as available
    "CO_MENTION",    # merely co-listed, no specific function (true residual)
    "OTHER",         # none fit — put the proposed sub-kind name in facet_detail
    "NA",            # no facet applies / not determinable
]

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
    "Then add a FACET — a filterable sub-kind UNDER the relation (this does NOT replace the "
    "relation; it refines it, and matters most for RELATED) — plus a short facet_detail "
    "naming the specific:\n"
    "- EXEMPLIFIES: cited as an instance/example of a category (surveys: 'approaches like "
    "[X]'). facet_detail = the category it is filed under.\n"
    "- COMPARES: positioned against/contrasted without contradicting. facet_detail = what is "
    "compared.\n"
    "- BACKGROUND: foundational concept / origin attribution. facet_detail = the concept.\n"
    "- MOTIVATION: cited to motivate the problem. facet_detail = the motivation.\n"
    "- APPLICATION: cited as an application domain. facet_detail = the domain.\n"
    "- CRITIQUES: flags a weakness/limitation of the cited work (short of contradiction). "
    "facet_detail = the weakness.\n"
    "- FUTURE_WORK: cited as an open problem or promising direction. facet_detail = the "
    "direction.\n"
    "- RESOURCE: points to a dataset/benchmark/tool as available (not used here). "
    "facet_detail = the resource.\n"
    "- CO_MENTION: merely co-listed, no specific function. facet_detail = ''.\n"
    "- OTHER: none of the above fits — invent the most accurate sub-kind name and put it in "
    "facet_detail (do NOT default to OTHER out of laziness; only when nothing fits).\n"
    "- NA: no facet applies. facet_detail = ''.\n"
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
    edges = [json.loads(l) for l in _IN.read_text().splitlines() if l.strip()]
    with_c = [e for e in edges if e["citances"]]
    without_c = [e for e in edges if not e["citances"]]
    print(f"{len(edges)} citation edges: {len(with_c)} with citances (typing), "
          f"{len(without_c)} without (-> semantic fallback in E-012)")

    typed = CitanceTyper().type_edges(with_c)
    rows = []
    for e, t in zip(with_c, typed):
        rows.append({
            "citing": e["citing"], "cited": e["cited"],
            "citing_title": e["citing_title"], "cited_title": e["cited_title"],
            "relation": t["relation"], "facet": t["facet"],
            "facet_detail": t["facet_detail"], "direction": "A_TO_B",  # A=citing
            "confidence": t["confidence"], "rationale": t["rationale"],
            "evidence": "citance", "s2_intents": e.get("intents") or [],
        })
    for e in without_c:
        rows.append({
            "citing": e["citing"], "cited": e["cited"],
            "citing_title": e["citing_title"], "cited_title": e["cited_title"],
            "relation": None, "facet": None, "facet_detail": "", "direction": "A_TO_B",
            "confidence": 0.0, "rationale": "", "evidence": "needs_semantic",
            "s2_intents": e.get("intents") or [],
        })
    _OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    from collections import Counter
    dist = Counter(r["relation"] for r in rows if r["relation"])
    related_facets = Counter(
        r["facet"] for r in rows if r["relation"] == "RELATED"
    )
    print(f"\n=== typed {len(typed)} cited edges ===")
    print("umbrella relation distribution:", dict(dist))
    print("FACETS within RELATED:", dict(related_facets))
    print(f"wrote {_OUT}")
    print("\n--- RELATED, now faceted (the umbrella broken into filterable sub-kinds) ---")
    for r in rows:
        if r["relation"] == "RELATED":
            detail = f" [{r['facet_detail']}]" if r["facet_detail"] else ""
            print(f"  RELATED/{r['facet']}{detail}: {r['citing_title'][:32]} -> {r['cited_title'][:32]}")


if __name__ == "__main__":
    main()
