"""Train + honestly evaluate the claim classifier on PubMed-RCT.

    python -m src.extraction.train                 # train, eval in-domain + OOD
    python -m src.extraction.train --epochs 3 --train-cap 8000
    python -m src.extraction.train --infer "We propose a new graph neural network."

Honest eval = in-domain test set (PubMed-RCT, natural distribution) AND an
out-of-distribution set of real CS sentences (src/extraction/ood.py). The OOD number
is the one that says whether this is usable for E-003.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader, Dataset
from transformers import DistilBertTokenizerFast

from . import data as data_mod
from .model import (
    ID2LABEL,
    LABEL2ID,
    MAX_LEN,
    ClaimClassifier,
    get_device,
    get_tokenizer,
)
from .ood import load_ood

_ROOT = Path(__file__).resolve().parents[2]
_SAVE_PATH = _ROOT / "claim_classifier_v2.pt"
_REPORT_PATH = _ROOT / "agents" / "engineer" / "workspace" / "e002_metrics.md"
_LABEL_NAMES = [ID2LABEL[i] for i in range(3)]


class _SentenceDataset(Dataset):
    def __init__(
        self,
        pairs: list[tuple[str, int]],
        tokenizer: DistilBertTokenizerFast,
    ) -> None:
        self.pairs = pairs
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        text, label = self.pairs[idx]
        enc = self.tokenizer(
            text,
            max_length=MAX_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def _run_epoch(
    model: ClaimClassifier,
    loader: DataLoader,
    device: torch.device,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None = None,
) -> tuple[float, list[int], list[int]]:
    train = optimizer is not None
    model.train() if train else model.eval()
    total_loss = 0.0
    preds: list[int] = []
    labels: list[int] = []
    with torch.set_grad_enabled(train):
        for batch in loader:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            y = batch["label"].to(device)
            if train:
                optimizer.zero_grad()
            logits = model(ids, mask)
            loss = criterion(logits, y)
            if train:
                loss.backward()
                optimizer.step()
            total_loss += loss.item()
            preds.extend(logits.argmax(-1).cpu().tolist())
            labels.extend(y.cpu().tolist())
    return total_loss / max(len(loader), 1), preds, labels


def _report(y_true: list[int], y_pred: list[int]) -> str:
    rep = classification_report(
        y_true, y_pred, target_names=_LABEL_NAMES, digits=3, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    cm_str = "confusion matrix (rows=true, cols=pred) [BACKGROUND, METHOD, CLAIM]:\n"
    for name, row in zip(_LABEL_NAMES, cm):
        cm_str += f"  {name:11s} {row.tolist()}\n"
    return f"{rep}\n{cm_str}"


def train(
    epochs: int = 3,
    batch_size: int = 32,
    lr: float = 2e-5,
    train_cap_per_class: int = 8000,
) -> None:
    device = get_device()
    print(f"Device: {device}")
    tokenizer = get_tokenizer()

    print("Loading PubMed-RCT (from source files)...")
    splits = data_mod.get_splits(train_cap_per_class=train_cap_per_class)
    print(data_mod.describe(splits))

    train_loader = DataLoader(
        _SentenceDataset(splits["train"], tokenizer),
        batch_size=batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        _SentenceDataset(splits["dev"], tokenizer), batch_size=batch_size
    )
    test_loader = DataLoader(
        _SentenceDataset(splits["test"], tokenizer), batch_size=batch_size
    )

    model = ClaimClassifier().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss()

    print(f"\nTraining {epochs} epochs...")
    best_val = float("inf")
    for epoch in range(1, epochs + 1):
        tr_loss, _, _ = _run_epoch(model, train_loader, device, criterion, optimizer)
        val_loss, vp, vl = _run_epoch(model, val_loader, device, criterion)
        from sklearn.metrics import f1_score

        val_f1 = f1_score(vl, vp, average="macro")
        print(
            f"  epoch {epoch}/{epochs}  train_loss={tr_loss:.4f}  "
            f"val_loss={val_loss:.4f}  val_macroF1={val_f1:.3f}"
        )
        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), _SAVE_PATH)
            print(f"    saved -> {_SAVE_PATH.name}")

    # ---- Honest evaluation ----
    model.load_state_dict(torch.load(_SAVE_PATH, map_location=device))

    _, tp, tl = _run_epoch(model, test_loader, device, criterion)
    indomain = _report(tl, tp)

    ood_pairs = load_ood()
    ood_loader = DataLoader(
        _SentenceDataset([(t, LABEL2ID[g]) for t, g in ood_pairs], tokenizer),
        batch_size=batch_size,
    )
    _, op, ol = _run_epoch(model, ood_loader, device, criterion)
    ood = _report(ol, op)

    out = (
        "# E-002 metrics — claim classifier on PubMed-RCT\n\n"
        f"_Generated by src.extraction.train (epochs={epochs}, "
        f"train_cap_per_class={train_cap_per_class})_\n\n"
        "## Data\n```\n" + data_mod.describe(splits) + "\n```\n\n"
        "## In-domain test (PubMed-RCT, natural distribution)\n```\n"
        + indomain
        + "```\n\n"
        f"## Out-of-distribution test ({len(ood_pairs)} hand-labeled CS sentences)\n"
        "_This is the number that decides whether the model is usable for E-003._\n```\n"
        + ood
        + "```\n"
    )
    _REPORT_PATH.write_text(out, encoding="utf-8")
    print("\n" + "=" * 70)
    print(out)
    print(f"Report written to {_REPORT_PATH}")


def infer(sentence: str) -> None:
    device = get_device()
    tokenizer = get_tokenizer()
    model = ClaimClassifier().to(device)
    model.load_state_dict(torch.load(_SAVE_PATH, map_location=device))
    model.eval()
    enc = tokenizer(
        sentence,
        max_length=MAX_LEN,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    with torch.no_grad():
        logits = model(
            enc["input_ids"].to(device), enc["attention_mask"].to(device)
        )
        probs = torch.softmax(logits, -1).squeeze(0)
        pid = int(probs.argmax())
    print(f"[{ID2LABEL[pid]}] ({probs[pid]:.3f})  {sentence}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--train-cap", type=int, default=8000, dest="train_cap")
    parser.add_argument("--infer", type=str, default=None)
    args = parser.parse_args()

    if args.infer is not None:
        infer(args.infer)
    else:
        train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            train_cap_per_class=args.train_cap,
        )


if __name__ == "__main__":
    main()
