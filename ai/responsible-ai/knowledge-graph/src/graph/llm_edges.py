"""LLM-based edge typer (Claude) — types claim pairs with the R-004 rich taxonomy.

R-005/E-006. Replaces the general-domain NLI typer (src/graph/edges.py), which forces
every pair into entailment/contradiction/neutral and mislabels "two different proposals"
as CONTRADICTS. The LLM can (a) emit NONE to prune false candidates and (b) name richer
relations. Each pair is judged WITH its source paper titles so cross-paper relations make
sense.

Interface: `type_pairs(pairs) -> list[dict]` where each input pair is a dict
{a_text, b_text, a_title, b_title} and each output is
{relation, direction, confidence, rationale}. Batched structured output.

Model: claude-opus-4-8 (haiku for bulk). Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
from typing import Any, List, cast

import anthropic

# Bulk default: haiku (~5x cheaper than opus). Pass model="claude-opus-4-8" for evals.
MODEL = "claude-haiku-4-5"
RELATIONS = [
    "SUPPORTS",
    "CONTRADICTS",
    "REFINES",
    "ADDRESSES_SAME_PROBLEM",
    "USES",
    "RELATED",
    "NONE",
]

_SYSTEM = (
    "You label the relationship between two claims (A and B) drawn from research-paper "
    "abstracts, for a claim knowledge graph. Direction is A→B. Use exactly one relation:\n"
    "- SUPPORTS: A's result/evidence backs B's claim.\n"
    "- CONTRADICTS: A's finding is logically incompatible with B's. Use sparingly — two "
    "papers each proposing a DIFFERENT method is NOT a contradiction.\n"
    "- REFINES: A improves, generalizes, or extends B's method or result.\n"
    "- ADDRESSES_SAME_PROBLEM: A and B tackle the same problem with different approaches "
    "(symmetric).\n"
    "- USES: A uses a method, dataset, or result introduced by B.\n"
    "- RELATED: same topic, but no stronger typed relation applies (symmetric).\n"
    "- NONE: not meaningfully related — they only share generic vocabulary. Prefer NONE "
    "over a weak guess.\n"
    "Set direction to A_TO_B, B_TO_A, or SYMMETRIC. Give calibrated confidence in [0,1] "
    "and a one-sentence rationale.\n\n"
    "Examples:\n"
    "A: 'We propose GraphSAGE, an inductive framework that generates node embeddings.' "
    "B: 'We propose Pinsage, a GCN for web-scale recommendation, and deploy it at "
    "Pinterest.' -> ADDRESSES_SAME_PROBLEM is wrong (different problems); the right answer "
    "is USES (B uses the GraphSAGE-style inductive idea), direction B_TO_A.\n"
    "A: 'We propose a new GNN model for graph-domain data.' B: 'We provide a comprehensive "
    "survey of GNN methods and applications.' -> RELATED, SYMMETRIC (a survey discussing "
    "the area, not using/refining this specific model).\n"
    "A: 'Our model reaches 95% accuracy on ImageNet.' B: 'Deep models struggle to exceed "
    "80% on ImageNet.' -> CONTRADICTS, A_TO_B."
)

_SCHEMA: object = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "relation": {"type": "string", "enum": RELATIONS},
                    "direction": {
                        "type": "string",
                        "enum": ["A_TO_B", "B_TO_A", "SYMMETRIC"],
                    },
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": ["index", "relation", "direction", "confidence", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

_DEFAULT: dict[str, Any] = {
    "relation": "NONE",
    "direction": "SYMMETRIC",
    "confidence": 0.0,
    "rationale": "",
}


class LLMEdgeTyper:
    def __init__(self, model: str = MODEL, batch_size: int = 10) -> None:
        self.client = anthropic.Anthropic()
        self.model = model
        self.batch_size = batch_size

    def _type_batch(self, pairs: list[dict[str, str]]) -> list[dict[str, Any]]:
        lines: List[str] = []
        for i, p in enumerate(pairs):
            lines.append(
                f"[{i}]\n  A ({p['a_title']}): {p['a_text']}\n"
                f"  B ({p['b_title']}): {p['b_text']}"
            )
        prompt = (
            f"Label the relation (A→B) for each of these {len(pairs)} claim pairs. "
            "Return one result per pair, matching its index.\n\n" + "\n\n".join(lines)
        )
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config=cast(Any, {"format": {"type": "json_schema", "schema": _SCHEMA}}),
        )
        text = next(b.text for b in resp.content if b.type == "text")
        by_index = {r["index"]: r for r in json.loads(text)["results"]}
        out: list[dict[str, Any]] = []
        for i in range(len(pairs)):
            r = by_index.get(i)
            out.append(
                {**_DEFAULT}
                if r is None
                else {
                    "relation": r["relation"],
                    "direction": r["direction"],
                    "confidence": float(r["confidence"]),
                    "rationale": r["rationale"],
                }
            )
        return out

    def type_pairs(self, pairs: list[dict[str, str]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i in range(0, len(pairs), self.batch_size):
            out.extend(self._type_batch(pairs[i : i + self.batch_size]))
        return out
