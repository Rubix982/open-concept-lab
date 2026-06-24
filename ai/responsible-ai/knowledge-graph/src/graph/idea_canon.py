"""E-018: collapse per-paper idea tags into a shared canonical vocabulary (Claude).

The paper cards (paper_cards.py) canonicalize ideas *independently per paper*, so the corpus
ends up with ~285 near-duplicate tags ("gcn" / "gcn model" / "graph convolutional networks").
This maps every raw tag to one shared canonical concept (~40), so idea filtering groups all
related papers and idea-level gap detection becomes possible.

    python -m src.graph.idea_canon            # -> data/processed/idea_canon.json

Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import cast, Any

import anthropic

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_CARDS = _PROC / "paper_cards.jsonl"
_OUT = _PROC / "idea_canon.json"

MODEL = "claude-haiku-4-5"

_SYSTEM = (
    "You normalize a flat list of research-concept tags into a SMALL shared vocabulary. "
    "Merge synonyms, plurals, abbreviations, and minor variants to ONE canonical form "
    "(e.g. 'gcn', 'gcn model', 'graph convolutional networks' -> 'graph convolution'; "
    "'recommender systems', 'recommendation systems' -> 'recommendation'). Canonical forms "
    "are short, lowercase noun phrases (1-3 words) naming the concept. Aim for roughly "
    "30-50 canonical concepts total — prefer merging over splitting, but do NOT merge "
    "genuinely distinct concepts (e.g. 'over-smoothing' != 'graph pooling'). Return one "
    "mapping entry for EVERY input tag."
)

_SCHEMA: object = {
    "type": "object",
    "properties": {
        "mapping": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw": {"type": "string"},
                    "canonical": {"type": "string"},
                },
                "required": ["raw", "canonical"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["mapping"],
    "additionalProperties": False,
}


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL,
                    help=f"Claude model (default {MODEL})")
    args = ap.parse_args()

    cards = [json.loads(l) for l in _CARDS.read_text().splitlines() if l.strip()]
    freq: Counter[str] = Counter(i for c in cards for i in c.get("ideas", []))
    raw = sorted(freq)
    print(f"{len(raw)} distinct idea tags → canonicalizing with {args.model}")

    client = anthropic.Anthropic()
    listing = "\n".join(f"- {t}  (×{freq[t]})" for t in raw)
    resp = client.messages.create(
        model=args.model,
        max_tokens=8192,
        system=_SYSTEM,
        messages=[{"role": "user", "content":
                   "Normalize every tag below to a canonical concept. The ×N is corpus "
                   "frequency (prefer the more frequent variant's name as canonical).\n\n"
                   + listing}],
        output_config=cast(Any, {"format": {"type": "json_schema", "schema": _SCHEMA}}),
    )
    text = next(b.text for b in resp.content if b.type == "text")
    mapping = {m["raw"]: m["canonical"].strip().lower()
               for m in json.loads(text)["mapping"] if m.get("raw")}
    # ensure every raw tag is covered (fall back to itself)
    for t in raw:
        mapping.setdefault(t, t)

    _OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=0))
    canon = Counter(mapping[t] for t in raw)
    print(f"\n=== {len(raw)} raw → {len(canon)} canonical concepts ===")
    for c, _ in canon.most_common(20):
        members = [t for t in raw if mapping[t] == c]
        print(f"  {c:28s} ← {len(members):2d}: {', '.join(members[:5])}"
              + (" …" if len(members) > 5 else ""))
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
