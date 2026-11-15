"""What NDIF is actually serving, and which of it this project can read.

Written on 2026-11-15, after [E-040] tried four models and Llama-3.1-405B came
back `CANT_ACCOMMODATE`. Until then the model list in this repo was a tuple
typed from memory into each run script. That is how a claim ends up naming a
model nobody checked was available.

The catalogue is read from `https://api.ndif.us/status`, which reports every
deployment with its serving level and, for anything loaded, its HuggingFace
config. Two things are then derived and they are **not** of equal standing:

- **`model_type` and layer count** are read straight from the served config, so
  they are facts about what the server has in memory.
- **Parameter count is an estimate.** For a COLD deployment there is no config
  at all and the only signal is the digits in the repo name, which is a label
  the uploader chose. For a loaded one the usual decoder arithmetic over
  hidden size, layers and the MLP width lands within a few per cent of the
  published figure, which is enough to sort by size and not enough to quote.
  The column is named `~params` for that reason and must not be cited.

**What `supported` means.** `editreach.arch` knows the path to the MLP output
projection for `llama` and `gptj` only. Reading the wrong module does not
raise — it returns plausible wrong numbers — so every other architecture here
is unavailable to this project until its path is added, however well NDIF
serves it. The column says which, and that is the real shortlist.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from editreach.arch import ARCH  # noqa: E402

STATUS = "https://api.ndif.us/status"

#: Sizes as written in a repo name: `-70B`, `-6b`, `-3.8B`, `-A3B` (active
#: params on a mixture-of-experts name, which is not the total and is skipped).
SIZE = re.compile(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)\s*[bB](?![a-zA-Z0-9])")


def declared_size(repo_id: str) -> float | None:
    """Billions of parameters as the repo *name* claims, or None."""
    found = SIZE.findall(repo_id.split("/")[-1])
    return max(float(x) for x in found) if found else None


def estimated_params(cfg: dict) -> float | None:
    """Billions of parameters from the served config. An estimate, not a count.

    Generic dense-decoder arithmetic: token embedding, then per layer an
    attention block with grouped-query key/value projections and a gated MLP.
    It ignores norms, biases and any mixture-of-experts routing, so it reads low
    on an MoE model — which is why a name-declared size wins when both exist.
    """
    h = cfg.get("hidden_size")
    L = cfg.get("num_hidden_layers")
    if not h or not L:
        return None
    v = cfg.get("vocab_size", 0)
    inter = cfg.get("intermediate_size") or 4 * h
    heads = cfg.get("num_attention_heads") or 1
    kv = cfg.get("num_key_value_heads") or heads
    head_dim = cfg.get("head_dim") or h // heads
    attn = h * (heads * head_dim) + 2 * h * (kv * head_dim) + (heads * head_dim) * h
    mlp = 3 * h * inter
    tied = cfg.get("tie_word_embeddings", False)
    embed = v * h * (1 if tied else 2)
    return (embed + L * (attn + mlp)) / 1e9


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-size", type=float, default=0.0,
                    help="billions of parameters; the project's floor is 8")
    ap.add_argument("--supported-only", action="store_true",
                    help="only architectures editreach.arch can read")
    ap.add_argument("--status", type=Path, default=None,
                    help="a saved /status payload instead of fetching one")
    ap.add_argument("--out", type=Path,
                    default=Path("results/ndif-catalogue.json"))
    a = ap.parse_args()

    if a.status:
        payload = json.loads(a.status.read_text())
    else:
        with urllib.request.urlopen(STATUS, timeout=60) as r:
            payload = json.loads(r.read())

    rows = []
    for d in payload["deployments"].values():
        repo = d.get("repo_id")
        if not repo:
            continue
        cfg = json.loads(d["config"]) if d.get("config") else {}
        est = estimated_params(cfg)
        name = declared_size(repo)
        mt = (cfg.get("model_type") or "").lower()
        rows.append({
            "repo_id": repo,
            "level": d.get("deployment_level"),
            "task": d.get("task"),
            "model_type": mt or None,
            "n_layers": cfg.get("num_hidden_layers"),
            "hidden_size": cfg.get("hidden_size"),
            # The name wins when both exist: it is what the publisher claims,
            # and the estimate reads low on a mixture-of-experts model.
            "size_b": name if name is not None else est,
            "size_from": "name" if name is not None else ("config" if est else None),
            "estimated_params_b": est,
            # Unknown architecture is not the same as unsupported: a COLD
            # deployment has no config, so its type is simply not yet known.
            "supported": (mt in ARCH) if mt else None,
        })

    rows.sort(key=lambda r: (-(r["size_b"] or 0), r["repo_id"]))
    shown = [r for r in rows
             if (r["size_b"] or 0) >= a.min_size
             and (not a.supported_only or r["supported"])]

    w = max((len(r["repo_id"]) for r in shown), default=10)
    print(f"{'repo_id':<{w}}  {'~params':>8}  {'src':<6}  {'level':<5}  "
          f"{'arch':<12}  {'L':>3}  read?")
    print("-" * (w + 48))
    for r in shown:
        size = f"{r['size_b']:.1f}B" if r["size_b"] else "?"
        ok = {True: "yes", False: "no", None: "?"}[r["supported"]]
        print(f"{r['repo_id']:<{w}}  {size:>8}  {r['size_from'] or '-':<6}  "
              f"{r['level'] or '?':<5}  {r['model_type'] or '?':<12}  "
              f"{r['n_layers'] or '':>3}  {ok}")

    big = [r for r in rows if (r["size_b"] or 0) > 8]
    readable = [r for r in big if r["supported"]]
    print()
    print(f"{len(rows)} deployments; {len(big)} above 8B; "
          f"{len(readable)} of those this project can read "
          f"({', '.join(sorted(ARCH))})")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "source": STATUS,
        "architectures_supported": sorted(ARCH),
        "n_deployments": len(rows),
        "n_above_8b": len(big),
        "n_above_8b_readable": len(readable),
        "note": ("Parameter counts are estimates — from the repo name, or from "
                 "decoder arithmetic over the served config. Not for citation."),
        "rows": rows,
    }, indent=1))
    print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
