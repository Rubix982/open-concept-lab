"""Claim extraction layer: classify sentences as BACKGROUND / METHOD / CLAIM.

Retrains the DistilBERT classifier on PubMed-RCT (real corpus, per R-001) and
evaluates honestly, including an out-of-distribution check on real ingested CS
sentences.

    python -m src.extraction.train          # train + evaluate (in-domain + OOD)
    python -m src.extraction.train --infer "some sentence"
"""

from .model import ID2LABEL, LABEL2ID, ClaimClassifier

__all__ = ["ClaimClassifier", "LABEL2ID", "ID2LABEL"]
