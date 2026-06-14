"""DistilBERT + linear head claim classifier (importable).

Same architecture as the original claim-classifier/train.py, factored out so training,
OOD eval, and the graph-construction stage (E-003) can all share one definition.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from transformers import DistilBertModel, DistilBertTokenizerFast

MODEL_NAME: str = "distilbert-base-uncased"
MAX_LEN: int = 64  # abstract sentences are short

LABEL2ID: dict[str, int] = {"BACKGROUND": 0, "METHOD": 1, "CLAIM": 2}
ID2LABEL: dict[int, str] = {v: k for k, v in LABEL2ID.items()}


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_tokenizer() -> DistilBertTokenizerFast:
    return DistilBertTokenizerFast.from_pretrained(MODEL_NAME)


class ClaimClassifier(nn.Module):
    """DistilBERT encoder + dropout + linear classification head over [CLS]."""

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
        cls_output: torch.Tensor = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits: torch.Tensor = self.classifier(cls_output)
        return logits
