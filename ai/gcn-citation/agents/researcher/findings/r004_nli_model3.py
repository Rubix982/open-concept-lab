"""
R-004: NLI Model Evaluation - Model 3 only (correct ID)
MoritzLaurer/deberta-v3-large-zeroshot-v2.0
"""

import json
import time
import torch
from transformers import pipeline

# Device setup
if torch.backends.mps.is_available():
    device_arg = "mps"
    print("Using MPS")
else:
    device_arg = "cpu"
    print("Using CPU")

PAIRS = [
    {
        "id": "pair1",
        "expected": "entailment",
        "label": "known_support",
        "claim_a": "Transformer models with multi-head self-attention outperform LSTM-based models on long-range sequence modeling tasks.",
        "claim_b": "Self-attention mechanisms enable transformers to capture dependencies across arbitrary sequence lengths, unlike recurrent architectures.",
    },
    {
        "id": "pair2",
        "expected": "contradiction",
        "label": "known_contradiction",
        "claim_a": "Batch normalization consistently improves training stability and generalization across deep neural network architectures.",
        "claim_b": "Batch normalization can degrade performance when batch size is small, and layer normalization is preferred in transformer architectures.",
    },
    {
        "id": "pair3",
        "expected": "neutral",
        "label": "known_neutral",
        "claim_a": "Graph neural networks aggregate neighbor features using message passing to learn node representations.",
        "claim_b": "Diffusion probabilistic models generate images by reversing a learned noising process.",
    },
]

model3_id = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
print(f"\n=== Model 3: {model3_id} ===")

load_error = None
device_used = device_arg
try:
    clf = pipeline(
        "zero-shot-classification",
        model=model3_id,
        device=device_arg,
    )
except Exception as e:
    load_error = str(e)
    print(f"  Load on {device_arg} failed: {e}, trying CPU...")
    try:
        clf = pipeline(
            "zero-shot-classification",
            model=model3_id,
            device="cpu",
        )
        device_used = "cpu"
    except Exception as e2:
        print(f"  FATAL on CPU too: {e2}")
        exit(1)

m3_results = []
for pair in PAIRS:
    hypothesis = pair["claim_b"]
    premise = pair["claim_a"]
    candidate_labels = ["entailment", "contradiction", "neutral"]
    try:
        t0 = time.perf_counter()
        out = clf(
            hypothesis,
            candidate_labels,
            hypothesis_template=f"Given that {premise}, this statement is {{}}.",
        )
        elapsed = time.perf_counter() - t0
        predicted = out["labels"][0]
        confidence = out["scores"][0]
        all_scores = dict(zip(out["labels"], out["scores"]))
        m3_results.append(
            {
                "pair_id": pair["id"],
                "expected": pair["expected"],
                "predicted": predicted,
                "confidence": round(confidence, 4),
                "all_scores": {k: round(v, 4) for k, v in all_scores.items()},
                "inference_time_s": round(elapsed, 3),
                "correct": predicted == pair["expected"],
                "device_used": device_used,
            }
        )
        print(
            f"  {pair['id']}: predicted={predicted} (conf={confidence:.3f}) in {elapsed:.2f}s [expected={pair['expected']}]"
        )
    except Exception as e:
        m3_results.append(
            {
                "pair_id": pair["id"],
                "expected": pair["expected"],
                "error": str(e),
                "device_used": device_used,
            }
        )
        print(f"  {pair['id']}: ERROR {e}")

# Load existing results and merge
results_path = "agents/researcher/findings/r004_nli_results.json"
with open(results_path) as f:
    results = json.load(f)

results[model3_id] = {
    "model_id": model3_id,
    "device_used": device_used,
    "mps_compatible": device_used == "mps",
    "load_error": load_error,
    "pairs": m3_results,
}

with open(results_path, "w") as f:
    json.dump(results, f, indent=2)

correct = sum(1 for p in m3_results if p.get("correct", False))
total = len([p for p in m3_results if "correct" in p])
print(
    f"\nModel 3: {correct}/{total} correct, device={device_used}, MPS={device_used == 'mps'}"
)
print(f"Updated {results_path}")
