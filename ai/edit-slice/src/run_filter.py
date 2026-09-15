"""CLI for the possession filter.

    python src/run_filter.py --config configs/possession_gptj.json

Configuration lives in a file, never in argv defaults (CLAUDE.md), and the config
that produced a result is written next to it. Runs are resumable: every item is
cached under results/cache/ before the next call, so an interrupted run resumes
rather than restarts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from possession import Edit, FilterConfig, Scorer, run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def build_scorer(cfg: FilterConfig) -> Scorer:
    if cfg.backend == "ndif":
        from remote import connect, score_pairs
        model = connect(cfg.model)
        return lambda pairs: score_pairs(model, pairs)
    from probing import load, score
    model, tok = load(cfg.model)
    return lambda pairs: [score(model, tok, p, c).logprob_mean for p, c in pairs]


def load_edits(spec: dict) -> list[Edit]:
    if spec.get("source") == "counterfact":
        return Edit.from_counterfact(limit=spec.get("limit"))
    return Edit.from_jsonl(Path(spec["path"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    raw = json.loads(args.config.read_text())
    edit_spec = raw.pop("_edits", {"source": "counterfact", "limit": 50})
    raw_reference = raw.pop("_candidate_reference", None)
    raw = {k: v for k, v in raw.items() if not k.startswith("_")}
    cfg = FilterConfig(**raw)

    edits = load_edits(edit_spec)
    # Candidates come from a REFERENCE vocabulary, not the edit set — deriving them
    # from a small edit set silently drops sparse relations and biases the rate.
    ref_spec = raw_reference or {"source": "counterfact"}
    reference = load_edits(ref_spec)
    log = setup("run_filter", config={**raw, "edits": len(edits),
                                      "edit_source": edit_spec.get("source", edit_spec.get("path")),
                                      "reference_items": len(reference),
                                      "fingerprint": cfg.fingerprint})
    log.info("%d edits | candidate vocabulary from %d reference items",
             len(edits), len(reference))

    # Keyed by everything that changes a number, not by model alone — otherwise a
    # 50-candidate result is silently served to an 8-candidate run.
    cache = ROOT / "results" / "cache" / f"{cfg.fingerprint.replace('|', '_')}.json"
    report = run(edits, cfg, build_scorer(cfg), cache_path=cache, reference=reference,
                 progress=lambda i, n: log.info("scored %d/%d", i, n) if i % 5 == 0 else None)

    for line in report.summary().splitlines():
        log.info("%s", line)
    # Named after the config, so two runs of the same model do not overwrite.
    out = args.out or ROOT / "results" / f"{args.config.stem}.json"
    report.to_json(out)
    log.info("written: %s  (config included)", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
