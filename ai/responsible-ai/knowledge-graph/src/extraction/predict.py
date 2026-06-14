"""Batch claim classification using the trained model (shared by E-003 build)."""

from __future__ import annotations

from pathlib import Path

import torch

from .model import ID2LABEL, MAX_LEN, ClaimClassifier, get_device, get_tokenizer

_DEFAULT_WEIGHTS = Path(__file__).resolve().parents[2] / "claim_classifier_v2.pt"


class ClaimTagger:
    """Loads the trained classifier once; tags batches of sentences."""

    def __init__(self, weights: str | Path | None = None) -> None:
        self.device = get_device()
        self.tokenizer = get_tokenizer()
        self.model = ClaimClassifier().to(self.device)
        path = Path(weights) if weights else _DEFAULT_WEIGHTS
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found — train first: python -m src.extraction.train"
            )
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.eval()

    def tag(self, texts: list[str], batch_size: int = 64) -> list[tuple[str, float]]:
        """Return [(label, confidence), ...] aligned with `texts`."""
        out: list[tuple[str, float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            enc = self.tokenizer(
                chunk,
                max_length=MAX_LEN,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            with torch.no_grad():
                logits = self.model(
                    enc["input_ids"].to(self.device),
                    enc["attention_mask"].to(self.device),
                )
                probs = torch.softmax(logits, dim=-1)
                conf, pred = probs.max(dim=-1)
            for p, c in zip(pred.cpu().tolist(), conf.cpu().tolist()):
                out.append((ID2LABEL[p], float(c)))
        return out
