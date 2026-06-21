"""E-014: per-paper contribution summary + canonical idea tags (Claude).

For every paper in the typed citation graph, write a one-sentence "what this paper
contributes" summary and 3-6 short idea tags, grounded ONLY in the paper's title and the
citances about it (the rationales/facet_details of edges where it is the CITED paper — i.e.
how the rest of the corpus describes it). No abstracts are fetched and nothing is invented.

    python -m src.graph.paper_cards            # bulk (haiku) -> paper_cards.jsonl
    python -m src.graph.paper_cards --limit 8  # sample -> paper_cards_sample_<model>.jsonl

Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import anthropic

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_EDGES = _PROC / "cited_edges_typed.jsonl"
_PAPERS = _PROC / "papers.jsonl"
_OUT = _PROC / "paper_cards.jsonl"

# Bulk default: haiku (a one-line summary + tags from given evidence is well within a small
# model). Use --model claude-opus-4-8 for a quality-ceiling sample.
MODEL = "claude-haiku-4-5"

_SYSTEM = (
    "You write a compact research-paper card from EVIDENCE ONLY (the paper's title and the "
    "ways other papers cite it). Never invent results, datasets, or numbers not present in "
    "the evidence. For each paper produce:\n"
    "- summary: ONE sentence, present tense, naming what the paper introduces or contributes "
    "(e.g. 'Introduces GraphSAGE, an inductive node-embedding method using neighborhood "
    "sampling and aggregation.'). If the evidence is thin, stay general but accurate; do not "
    "fabricate specifics.\n"
    "- ideas: 3-6 short canonical concept tags (2-4 words, lowercase, deduplicated) naming "
    "the key methods/concepts the paper is associated with (e.g. 'graph convolution', "
    "'inductive learning', 'neighborhood aggregation'). Prefer the canonical name over "
    "near-duplicates ('gcn' not 'gcn model'/'gcn baseline')."
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
                    "summary": {"type": "string"},
                    "ideas": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["index", "summary", "ideas"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def _evidence(papers: dict[str, dict], by_cited: dict[str, list[dict]],
              pid: str) -> dict[str, Any]:
    """Assemble the title + 'cited as' details + citance rationales for one paper."""
    title = papers.get(pid, {}).get("title") or pid
    inc = by_cited.get(pid, [])
    details = Counter(e["facet_detail"].strip() for e in inc
                      if (e.get("facet_detail") or "").strip())
    # strongest rationales first: prefer USES/REFINES/SUPPORTS over RELATED/NONE, then conf
    rank = {"USES": 0, "REFINES": 0, "SUPPORTS": 1, "CONTRADICTS": 1,
            "ADDRESSES_SAME_PROBLEM": 2, "RELATED": 3, "NONE": 4}
    rats = sorted(
        (e for e in inc if (e.get("rationale") or "").strip()),
        key=lambda e: (rank.get(e.get("relation"), 5), -float(e.get("confidence") or 0)),
    )
    return {
        "title": title,
        "cited_as": [d for d, _ in details.most_common(10)],
        "rationales": [e["rationale"].strip()[:240] for e in rats[:6]],
    }


class CardWriter:
    def __init__(self, model: str = MODEL, batch_size: int = 8) -> None:
        self.client = anthropic.Anthropic()
        self.model = model
        self.batch_size = batch_size

    def _batch(self, ev: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lines = []
        for i, e in enumerate(ev):
            cited_as = ", ".join(e["cited_as"]) or "(none)"
            cit = "\n     - ".join(e["rationales"]) if e["rationales"] else "(none)"
            lines.append(
                f"[{i}] title='{e['title']}'\n     cited as: {cited_as}\n"
                f"     citances about it:\n     - {cit}"
            )
        prompt = (
            f"Write a card (summary + ideas) for each of these {len(ev)} papers. "
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
        for i in range(len(ev)):
            r = by_index.get(i)
            out.append({"summary": "", "ideas": []} if r is None
                       else {"summary": r["summary"].strip(),
                             "ideas": [s.strip().lower() for s in r["ideas"] if s.strip()]})
        return out

    def write(self, ev: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for i in range(0, len(ev), self.batch_size):
            out.extend(self._batch(ev[i : i + self.batch_size]))
        return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="card the first N papers (sample); writes a *_sample file")
    ap.add_argument("--model", default=MODEL,
                    help=f"Claude model (default {MODEL}; use claude-opus-4-8 for a sample)")
    args = ap.parse_args()

    papers = {p["paper_id"]: p for p in
              (json.loads(l) for l in _PAPERS.read_text().splitlines() if l.strip())}
    edges = [json.loads(l) for l in _EDGES.read_text().splitlines() if l.strip()]
    edges = [e for e in edges if e.get("relation")]

    by_cited: dict[str, list[dict]] = defaultdict(list)
    node_ids: set[str] = set()
    for e in edges:
        by_cited[e["cited"]].append(e)
        node_ids.add(e["citing"])
        node_ids.add(e["cited"])
    # order: most-cited first (richest evidence, and the papers users click first)
    order = sorted(node_ids, key=lambda n: -len(by_cited.get(n, [])))

    sample = args.limit is not None
    target = order[: args.limit] if sample else order
    ev = [{"pid": pid, **_evidence(papers, by_cited, pid)} for pid in target]
    model_tag = args.model.split("-")[1] if "-" in args.model else args.model
    out_path = _OUT.with_name(f"paper_cards_sample_{model_tag}.jsonl") if sample else _OUT
    print(f"{len(node_ids)} papers in graph; carding {len(target)} with {args.model}"
          f"{' (SAMPLE)' if sample else ''}")

    cards = CardWriter(model=args.model).write(ev)
    rows = [{"paper_id": e["pid"], "summary": c["summary"], "ideas": c["ideas"]}
            for e, c in zip(ev, cards)]
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    n_sum = sum(1 for r in rows if r["summary"])
    all_ideas = Counter(i for r in rows for i in r["ideas"])
    print(f"\n=== {len(rows)} cards: {n_sum} with summaries, "
          f"{len(all_ideas)} distinct ideas ===")
    for r in rows[:5]:
        print(f"  • {papers.get(r['paper_id'], {}).get('title', r['paper_id'])[:44]}")
        print(f"    {r['summary']}")
        print(f"    ideas: {', '.join(r['ideas'])}")
    print(f"\ntop ideas: {[i for i, _ in all_ideas.most_common(12)]}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
