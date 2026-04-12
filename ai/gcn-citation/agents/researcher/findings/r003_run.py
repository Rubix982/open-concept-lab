"""
R-003: L2 extraction prompt design and validation.
Run this script directly: python3 agents/researcher/findings/r003_run.py
"""

import json
import sys
import random
import datetime
import pandas as pd
import requests

# ── 1. Sample 5 diverse papers ────────────────────────────────────────────────

df = pd.read_parquet("data/pipeline/arxiv_10k.parquet")

# Target subfields mapped to primary_category prefixes
targets = {
    "NLP / language modeling": ["cs.CL"],
    "Computer Vision": ["cs.CV"],
    "Optimization / theory": ["math.OC", "cs.LG", "stat.ML"],
    "Graph learning / GNN": ["cs.LG", "cs.AI"],
    "Statistics / probabilistic ML": ["stat.ML", "stat.TH", "stat.ME"],
}


# For GNN paper we look for keywords in title/abstract
def pick_one(df, cats, seed, keywords=None):
    sub = df[df["primary_category"].isin(cats)].copy()
    if keywords:
        mask = sub["title"].str.contains(
            "|".join(keywords), case=False, na=False
        ) | sub["abstract"].str.contains("|".join(keywords), case=False, na=False)
        sub = sub[mask]
    if sub.empty:
        sub = df[df["primary_category"].isin(cats)]
    return sub.sample(1, random_state=seed).iloc[0]


random.seed(42)

papers = [
    pick_one(df, ["cs.CL"], seed=7),
    pick_one(df, ["cs.CV"], seed=13),
    pick_one(
        df,
        ["math.OC", "cs.LG"],
        seed=21,
        keywords=["convergence", "gradient", "optimization", "sgd", "adam"],
    ),
    pick_one(
        df,
        ["cs.LG", "cs.AI"],
        seed=37,
        keywords=["graph", "node", "GNN", "message passing", "attention", "sage"],
    ),
    pick_one(df, ["stat.ML"], seed=55),
]

print("=" * 70)
print("STEP 1 — Sampled papers")
print("=" * 70)
for i, p in enumerate(papers, 1):
    print(f"\n[{i}] {p['arxiv_id']} | {p['primary_category']}")
    print(f"    Title: {p['title']}")
    print(f"    Abstract[:200]: {p['abstract'][:200]!r}")

# ── 2. Prompt design ──────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
You are a research assistant specializing in AI, machine learning, and computer science. \
Your task is to extract a structured summary from an arXiv paper.

Read the title and abstract below, then output ONLY a single JSON object that matches \
the schema exactly. Do NOT add any explanation, markdown, code fences, preamble, or \
commentary. Output raw JSON only.

Schema:
{{
  "contribution": "<ONE sentence: the main contribution of this paper>",
  "method": "<The specific technique, architecture, or algorithm used — be precise, \
not generic (e.g. 'transformer encoder with cross-attention' not 'deep learning')>",
  "datasets": ["<dataset name>", "..."],
  "key_findings": [
    "<finding 1 — include numbers/metrics where available>",
    "<finding 2>",
    "<finding 3>"
  ],
  "limitations": "<Known constraints, scope limitations, or null if none stated>",
  "domain_tags": ["<2-4 specific tags, e.g. NLP, transformers, language_modeling>"],
  "related_methods": ["<name of related technique or paper>", "..."]
}}

Rules:
- "contribution" must be one sentence only.
- "method" must name the specific technique, not just "neural network" or "deep learning".
- "key_findings" must contain exactly 3 items; include numeric results if stated.
- "datasets" must be an empty list [] if no datasets are named in the abstract.
- "domain_tags" must contain 2 to 4 tags maximum.
- Output JSON only. No explanation. No markdown. No code fences.

Paper title: {title}

Abstract:
{abstract}

JSON:"""

# ── 3. Call Ollama ────────────────────────────────────────────────────────────


def call_ollama(prompt: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["response"]


results = []

print("\n" + "=" * 70)
print("STEP 3 — Calling Ollama for each paper")
print("=" * 70)

for i, paper in enumerate(papers, 1):
    label = [
        "NLP / language modeling",
        "Computer Vision",
        "Optimization / theory",
        "Graph learning / GNN",
        "Statistics / probabilistic ML",
    ][i - 1]

    print(f"\n[{i}/5] {label}")
    print(f"  arxiv_id : {paper['arxiv_id']}")
    print(f"  title    : {paper['title'][:80]}")

    prompt = PROMPT_TEMPLATE.format(
        title=paper["title"],
        abstract=paper["abstract"],
    )

    try:
        raw = call_ollama(prompt)
        parsed = json.loads(raw)
        parse_ok = True
        parse_error = None
    except json.JSONDecodeError as e:
        parsed = None
        parse_ok = False
        parse_error = str(e)
    except Exception as e:
        raw = f"ERROR: {e}"
        parsed = None
        parse_ok = False
        parse_error = str(e)

    result = {
        "paper_idx": i,
        "subfield": label,
        "arxiv_id": paper["arxiv_id"],
        "title": paper["title"],
        "abstract": paper["abstract"],
        "prompt": prompt,
        "raw_response": raw if isinstance(raw, str) else json.dumps(raw),
        "parsed": parsed,
        "parse_ok": parse_ok,
        "parse_error": parse_error,
    }
    results.append(result)

    if parse_ok:
        print(f"  parse    : OK")
        print(f"  contribution : {parsed.get('contribution', 'MISSING')}")
        print(f"  method       : {parsed.get('method', 'MISSING')}")
        print(f"  datasets     : {parsed.get('datasets', 'MISSING')}")
        print(f"  key_findings : {parsed.get('key_findings', 'MISSING')}")
        print(f"  limitations  : {parsed.get('limitations', 'MISSING')}")
        print(f"  domain_tags  : {parsed.get('domain_tags', 'MISSING')}")
        print(f"  related_methods: {parsed.get('related_methods', 'MISSING')}")
    else:
        print(f"  parse    : FAILED — {parse_error}")
        print(f"  raw      : {raw[:300]!r}")

# ── 4. Save raw extractions ───────────────────────────────────────────────────

out_path = "agents/researcher/findings/r003_l2_extractions.json"
with open(out_path, "w") as f:
    json.dump(
        {
            "ticket": "R-003",
            "extracted_at": datetime.datetime.utcnow().isoformat() + "Z",
            "model": "qwen2.5-coder:7b",
            "prompt_template": PROMPT_TEMPLATE,
            "results": results,
        },
        f,
        indent=2,
    )

print(f"\n\nSaved extractions to {out_path}")
print("\nDone — review output above to complete Step 4 quality evaluation.")
