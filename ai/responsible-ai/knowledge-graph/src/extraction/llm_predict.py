"""LLM-based claim classifier (Claude) — drop-in alternative to the DistilBERT tagger.

R-003: the PubMed-RCT DistilBERT transfers poorly to CS text (OOD macro-F1 0.571).
A few-shot Claude classifier should be domain-general. This exposes the same
`.tag(texts) -> list[(label, confidence)]` interface as
`src.extraction.predict.ClaimTagger`, so `src/graph/build.py` can use it unchanged.

Uses batched structured output (one request per batch of sentences) for efficiency.
Model: claude-opus-4-8 (best model → establishes the true quality ceiling for the
DistilBERT-vs-LLM comparison). Swap to claude-haiku-4-5 for cheaper bulk runs.

Requires ANTHROPIC_API_KEY in the environment.
"""

from __future__ import annotations

import json

import anthropic

MODEL = "claude-opus-4-8"
LABELS = ["BACKGROUND", "METHOD", "CLAIM"]

_SYSTEM = (
    "You classify individual sentences from research-paper abstracts by their "
    "rhetorical role, for a claim-extraction pipeline. Use exactly one label per "
    "sentence:\n"
    "- BACKGROUND: context, motivation, prior work, problem statement, definitions.\n"
    "- METHOD: what the authors did/built — techniques, architecture, training setup, "
    "datasets used, implementation/availability details.\n"
    "- CLAIM: the paper's own contributions and findings — 'we propose X', 'we show', "
    "'achieves', results, conclusions drawn from results.\n"
    "Judge each sentence on its own. Domain is arbitrary (CS, biomed, etc.). "
    "Return calibrated confidence in [0,1]."
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
                    "label": {"type": "string", "enum": LABELS},
                    "confidence": {"type": "number"},
                },
                "required": ["index", "label", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


class LLMClaimTagger:
    def __init__(self, model: str = MODEL, batch_size: int = 15) -> None:
        self.client = anthropic.Anthropic()
        self.model = model
        self.batch_size = batch_size

    def _tag_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        numbered = "\n".join(f"[{i}] {t}" for i, t in enumerate(texts))
        prompt = (
            f"Classify each of the following {len(texts)} sentences. Return one "
            "result per sentence, matching its index.\n\n" + numbered
        )
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        )
        text = next(b.text for b in resp.content if b.type == "text")
        parsed = json.loads(text)
        by_index = {r["index"]: r for r in parsed["results"]}
        out: list[tuple[str, float]] = []
        for i in range(len(texts)):
            r = by_index.get(i)
            if r is None:  # model dropped one — default conservatively
                out.append(("BACKGROUND", 0.0))
            else:
                out.append((r["label"], float(r["confidence"])))
        return out

    def tag(self, texts: list[str], batch_size: int | None = None) -> list[tuple[str, float]]:
        bs = batch_size or self.batch_size
        out: list[tuple[str, float]] = []
        for i in range(0, len(texts), bs):
            out.extend(self._tag_batch(texts[i : i + bs]))
        return out
