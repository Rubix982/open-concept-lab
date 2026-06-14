"""R-003: compare claim taggers on the hand-labeled OOD CS set.

    python -m src.extraction.eval_ood

Reports macro-F1 + per-class metrics for the DistilBERT tagger and the LLM tagger
against the 33 hand-labeled CS sentences (src/extraction/ood.py).
"""

from __future__ import annotations

from sklearn.metrics import classification_report, f1_score

from .ood import load_ood

_LABELS = ["BACKGROUND", "METHOD", "CLAIM"]


def _report(name: str, golds: list[str], preds: list[str]) -> str:
    rep = classification_report(
        golds, preds, labels=_LABELS, digits=3, zero_division=0
    )
    macro = f1_score(golds, preds, labels=_LABELS, average="macro", zero_division=0)
    return f"### {name}  (macro-F1 = {macro:.3f})\n{rep}"


def main() -> None:
    ood = load_ood()
    texts = [t for t, _ in ood]
    golds = [g for _, g in ood]
    print(f"OOD set: {len(ood)} hand-labeled CS sentences\n")

    blocks: list[str] = []

    # DistilBERT (PubMed-RCT trained)
    try:
        from .predict import ClaimTagger

        db = ClaimTagger()
        db_preds = [lbl for lbl, _ in db.tag(texts)]
        blocks.append(_report("DistilBERT (PubMed-RCT)", golds, db_preds))
    except Exception as e:  # noqa: BLE001
        blocks.append(f"### DistilBERT — skipped: {e}")

    # LLM (Claude)
    try:
        from .llm_predict import MODEL, LLMClaimTagger

        llm = LLMClaimTagger()
        llm_preds = [lbl for lbl, _ in llm.tag(texts)]
        blocks.append(_report(f"LLM ({MODEL})", golds, llm_preds))
    except Exception as e:  # noqa: BLE001
        blocks.append(f"### LLM — skipped: {e}")

    print("\n\n".join(blocks))


if __name__ == "__main__":
    main()
