"""
claim-classifier/train.py

Fine-tune DistilBERT to classify sentences in research papers as:
  - CLAIM      : a finding, assertion, or contribution the paper is making
  - BACKGROUND : context, motivation, prior work, related work
  - METHOD     : description of process, technique, or experimental setup

This is the claim extraction layer of the knowledge infrastructure.
Identifies which sentences are worth putting into the knowledge graph.

Architecture:
  DistilBERT (pretrained) → [CLS] pooling → Linear(768, 3) → softmax

Usage:
  python train.py          # train and evaluate
  python train.py --infer  # load saved model and classify new sentences
"""

import argparse
from pathlib import Path
from typing import NamedTuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import DistilBertModel, DistilBertTokenizerFast
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_NAME: str = "distilbert-base-uncased"
MAX_LEN: int = 128
BATCH_SIZE: int = 16
EPOCHS: int = 4
LR: float = 2e-5
DEVICE: torch.device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)
SAVE_PATH: Path = Path("claim_classifier.pt")

LABEL2ID: dict[str, int] = {"BACKGROUND": 0, "METHOD": 1, "CLAIM": 2}
ID2LABEL: dict[int, str] = {v: k for k, v in LABEL2ID.items()}


# ---------------------------------------------------------------------------
# Synthetic training data
# Real deployment: replace with SciArg, ACL-ARC, or your own annotated corpus
# ---------------------------------------------------------------------------
RAW_DATA: list[tuple[str, str]] = [
    # BACKGROUND
    ("Neural networks have been widely used for natural language processing tasks.",
     "BACKGROUND"),
    ("Prior work has demonstrated that attention mechanisms improve performance.",
     "BACKGROUND"),
    ("The field of machine learning has grown significantly over the past decade.",
     "BACKGROUND"),
    ("Transformer models were introduced by Vaswani et al. in 2017.",
     "BACKGROUND"),
    ("Existing approaches to text classification rely on handcrafted features.",
     "BACKGROUND"),
    ("Previous studies have shown that data augmentation can reduce overfitting.",
     "BACKGROUND"),
    ("Large language models are typically trained on web-scale corpora.",
     "BACKGROUND"),
    ("Knowledge graphs have been used to represent structured information.",
     "BACKGROUND"),
    ("Most prior work focuses on supervised learning with labeled datasets.",
     "BACKGROUND"),
    ("The problem of catastrophic forgetting has been studied in continual learning.",
     "BACKGROUND"),

    # METHOD
    ("We fine-tune a pretrained BERT model on our annotated dataset.",
     "METHOD"),
    ("We split the data 80/20 into training and validation sets.",
     "METHOD"),
    ("The model is trained using the AdamW optimizer with a learning rate of 2e-5.",
     "METHOD"),
    ("We apply dropout with probability 0.1 to the final hidden layer.",
     "METHOD"),
    ("Sentences are tokenized using the WordPiece tokenizer with a max length of 128.",
     "METHOD"),
    ("We evaluate performance using macro-averaged F1 score.",
     "METHOD"),
    ("Each experiment is repeated five times with different random seeds.",
     "METHOD"),
    ("We use a linear layer on top of the [CLS] token representation for classification.",
     "METHOD"),
    ("Training is performed on a single GPU with a batch size of 32.",
     "METHOD"),
    ("We threshold cosine similarity at 0.75 to construct the knowledge graph edges.",
     "METHOD"),

    # CLAIM
    ("Our model achieves state-of-the-art performance on three benchmark datasets.",
     "CLAIM"),
    ("We show that fine-tuning on domain-specific data improves classification accuracy.",
     "CLAIM"),
    ("The results demonstrate that claim extraction is feasible with limited supervision.",
     "CLAIM"),
    ("Our approach reduces labeling cost by 40% while maintaining comparable performance.",
     "CLAIM"),
    ("We find that sentence-level context is more informative than word-level features.",
     "CLAIM"),
    ("The proposed method generalises across scientific domains without retraining.",
     "CLAIM"),
    ("Our analysis reveals that most papers contain fewer than five distinct claims.",
     "CLAIM"),
    ("Fine-tuning outperforms zero-shot classification on this task by a significant margin.",
     "CLAIM"),
    ("The knowledge graph constructed from extracted claims improves downstream retrieval.",
     "CLAIM"),
    ("We demonstrate that consent-based data collection does not reduce model quality.",
     "CLAIM"),

    # Additional examples for balance
    ("Related work has addressed similar problems in the biomedical domain.",
     "BACKGROUND"),
    ("The dataset consists of 10,000 sentences from 500 computer science papers.",
     "METHOD"),
    ("Our model is the first to jointly extract claims and their supporting evidence.",
     "CLAIM"),
    ("Previous approaches ignore the rhetorical structure of scientific arguments.",
     "BACKGROUND"),
    ("We manually annotated 1,000 sentences to create the training set.",
     "METHOD"),
    ("The precision of claim detection exceeds 85% across all domains tested.",
     "CLAIM"),
    ("Sentence embeddings are computed using a pretrained sentence transformer.",
     "METHOD"),
    ("Graph-based representations have shown promise for scientific literature mining.",
     "BACKGROUND"),
    ("Our error analysis shows that boundary sentences are the hardest to classify.",
     "CLAIM"),
    ("We compare against five baseline methods from the recent literature.",
     "METHOD"),
]


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class SentenceRecord(NamedTuple):
    text: str
    label: int


class ClaimDataset(Dataset):
    def __init__(
        self,
        records: list[SentenceRecord],
        tokenizer: DistilBertTokenizerFast,
        max_len: int,
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        record = self.records[idx]
        encoding = self.tokenizer(
            record.text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(record.label, dtype=torch.long),
        }


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class ClaimClassifier(nn.Module):
    """DistilBERT + linear classification head."""

    def __init__(self, num_classes: int = 3, dropout: float = 0.1) -> None:
        super().__init__()
        self.bert = DistilBertModel.from_pretrained(MODEL_NAME)
        hidden: int = self.bert.config.hidden_size  # 768
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden, num_classes)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # [CLS] token is first position in last hidden state
        cls_output: torch.Tensor = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits: torch.Tensor = self.classifier(cls_output)
        return logits


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_epoch(
    model: ClaimClassifier,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
) -> float:
    model.train()
    total_loss: float = 0.0
    for batch in loader:
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["label"].to(DEVICE)

        optimizer.zero_grad()
        logits = model(input_ids, attention_mask)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(loader)


def evaluate(
    model: ClaimClassifier,
    loader: DataLoader,
) -> tuple[float, list[int], list[int]]:
    model.eval()
    all_preds: list[int] = []
    all_labels: list[int] = []
    total_loss: float = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)

            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
            total_loss += loss.item()

            preds = logits.argmax(dim=-1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().tolist())

    return total_loss / len(loader), all_preds, all_labels


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def classify_sentences(
    sentences: list[str],
    model: ClaimClassifier,
    tokenizer: DistilBertTokenizerFast,
) -> list[dict[str, str | float]]:
    """Classify a list of sentences. Returns label and confidence per sentence."""
    model.eval()
    results: list[dict[str, str | float]] = []

    for sentence in sentences:
        encoding = tokenizer(
            sentence,
            max_length=MAX_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].to(DEVICE)
        attention_mask = encoding["attention_mask"].to(DEVICE)

        with torch.no_grad():
            logits = model(input_ids, attention_mask)
            probs = torch.softmax(logits, dim=-1).squeeze(0)
            pred_id = probs.argmax().item()
            confidence = probs[pred_id].item()

        results.append({
            "sentence": sentence,
            "label": ID2LABEL[pred_id],
            "confidence": round(confidence, 4),
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(infer_mode: bool = False) -> None:
    print(f"Device: {DEVICE}")

    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    if infer_mode:
        print("\n--- Inference mode ---")
        if not SAVE_PATH.exists():
            print(f"No saved model at {SAVE_PATH}. Run training first.")
            return

        model = ClaimClassifier().to(DEVICE)
        model.load_state_dict(torch.load(SAVE_PATH, map_location=DEVICE))

        test_sentences = [
            "We propose a novel method for extracting claims from scientific papers.",
            "Prior work has explored graph-based representations of knowledge.",
            "The model is evaluated on the SciArg benchmark dataset.",
            "Our results show a 15% improvement over the baseline.",
            "Sentence transformers were introduced to produce fixed-length embeddings.",
        ]

        results = classify_sentences(test_sentences, model, tokenizer)
        print(f"\n{'Sentence':<60} {'Label':<12} {'Conf':>6}")
        print("-" * 82)
        for r in results:
            sentence = str(r["sentence"])[:58]
            print(f"{sentence:<60} {str(r['label']):<12} {r['confidence']:>6.3f}")
        return

    # --- Prepare data ---
    records = [
        SentenceRecord(text=text, label=LABEL2ID[label])
        for text, label in RAW_DATA
    ]
    train_records, val_records = train_test_split(
        records, test_size=0.25, random_state=42,
        stratify=[r.label for r in records]
    )

    train_dataset = ClaimDataset(train_records, tokenizer, MAX_LEN)
    val_dataset = ClaimDataset(val_records, tokenizer, MAX_LEN)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    print(f"Train: {len(train_dataset)} | Val: {len(val_dataset)}")

    # --- Model, optimiser, loss ---
    model = ClaimClassifier().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss()

    # --- Training loop ---
    print(f"\nTraining for {EPOCHS} epochs...\n")
    best_val_loss: float = float("inf")

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss, val_preds, val_labels = evaluate(model, val_loader)

        print(
            f"Epoch {epoch}/{EPOCHS}  "
            f"train_loss={train_loss:.4f}  val_loss={val_loss:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), SAVE_PATH)
            print(f"  ✓ Saved best model → {SAVE_PATH}")

    # --- Final evaluation ---
    print("\n--- Classification Report (validation set) ---")
    label_names = [ID2LABEL[i] for i in range(3)]
    print(classification_report(val_labels, val_preds, target_names=label_names))

    # --- Quick inference demo ---
    print("--- Inference demo ---")
    demo_sentences = [
        "We show that our approach outperforms all baselines on three datasets.",
        "The dataset was collected from ArXiv papers published between 2018 and 2023.",
        "We use a transformer encoder with 12 attention heads.",
    ]
    results = classify_sentences(demo_sentences, model, tokenizer)
    for r in results:
        sentence = str(r["sentence"])[:60]
        print(f"  [{r['label']:>10}] ({r['confidence']:.3f})  {sentence}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--infer", action="store_true",
                        help="Load saved model and run inference demo")
    args = parser.parse_args()
    main(infer_mode=args.infer)
