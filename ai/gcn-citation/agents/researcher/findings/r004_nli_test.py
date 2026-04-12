"""
R-004: NLI Model Evaluation Script
Tests three NLI models on 3 claim pairs for contradiction/support classification.
Runs on Apple M2 MPS where possible, falls back to CPU.
"""

import json
import time
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Device setup
if torch.backends.mps.is_available():
    device_label = "mps"
    # pipeline uses device index; for MPS use "mps" string via device kwarg
    device_arg = "mps"
    device_id = torch.device("mps")
    print(f"MPS available: {torch.backends.mps.is_available()}")
else:
    device_label = "cpu"
    device_arg = "cpu"
    device_id = torch.device("cpu")
    print("MPS not available, using CPU")

# -------- Test Pairs --------
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

results = {}


# -------- Helper --------
def run_zeroshot_pipeline(model_id, pairs, device):
    """Use zero-shot-classification pipeline (for cross-encoder NLI models)."""
    model_results = []
    load_error = None
    try:
        clf = pipeline(
            "zero-shot-classification",
            model=model_id,
            device=device,
        )
    except Exception as e:
        load_error = str(e)
        # Try CPU fallback
        print(f"  Load on {device} failed: {e}, trying CPU...")
        clf = pipeline(
            "zero-shot-classification",
            model=model_id,
            device="cpu",
        )
        device = "cpu"

    for pair in pairs:
        premise = pair["claim_a"]
        hypothesis = pair["claim_b"]
        # candidate labels = NLI classes
        candidate_labels = ["entailment", "contradiction", "neutral"]
        try:
            t0 = time.perf_counter()
            # For cross-encoder NLI: use hypothesis_template that injects premise
            # We want: does hypothesis follow from / contradict premise?
            # Pass premise as candidate label via hypothesis_template wrapping
            out = clf(
                hypothesis,
                candidate_labels,
                hypothesis_template=f"Given that {premise}, this statement is {{}}.",
            )
            elapsed = time.perf_counter() - t0

            # out["labels"] sorted by score descending
            predicted = out["labels"][0]
            confidence = out["scores"][0]
            all_scores = dict(zip(out["labels"], out["scores"]))

            model_results.append(
                {
                    "pair_id": pair["id"],
                    "expected": pair["expected"],
                    "predicted": predicted,
                    "confidence": round(confidence, 4),
                    "all_scores": {k: round(v, 4) for k, v in all_scores.items()},
                    "inference_time_s": round(elapsed, 3),
                    "correct": predicted == pair["expected"],
                    "device_used": device,
                }
            )
            print(
                f"  {pair['id']}: predicted={predicted} (conf={confidence:.3f}) in {elapsed:.2f}s"
            )
        except Exception as e:
            model_results.append(
                {
                    "pair_id": pair["id"],
                    "expected": pair["expected"],
                    "error": str(e),
                    "device_used": device,
                }
            )
            print(f"  {pair['id']}: ERROR {e}")

    return model_results, device, load_error


def run_textclassification_pipeline(model_id, pairs, device):
    """
    Use text-classification with explicit NLI label mapping.
    For facebook/bart-large-mnli which outputs LABEL_0/1/2 or entailment/neutral/contradiction.
    Uses zero-shot-classification which gives cleaner interface.
    """
    return run_zeroshot_pipeline(model_id, pairs, device)


# -------- Model 1: cross-encoder/nli-deberta-v3-small --------
print("\n=== Model 1: cross-encoder/nli-deberta-v3-small ===")
model1_id = "cross-encoder/nli-deberta-v3-small"
try:
    m1_results, m1_device, m1_load_err = run_zeroshot_pipeline(
        model1_id, PAIRS, device_arg
    )
    results["cross-encoder/nli-deberta-v3-small"] = {
        "model_id": model1_id,
        "device_used": m1_device,
        "mps_compatible": m1_device == "mps",
        "load_error": m1_load_err,
        "pairs": m1_results,
    }
except Exception as e:
    print(f"  FATAL: {e}")
    results["cross-encoder/nli-deberta-v3-small"] = {
        "model_id": model1_id,
        "fatal_error": str(e),
        "mps_compatible": False,
    }

# -------- Model 2: facebook/bart-large-mnli --------
print("\n=== Model 2: facebook/bart-large-mnli ===")
model2_id = "facebook/bart-large-mnli"
try:
    m2_results, m2_device, m2_load_err = run_zeroshot_pipeline(
        model2_id, PAIRS, device_arg
    )
    results["facebook/bart-large-mnli"] = {
        "model_id": model2_id,
        "device_used": m2_device,
        "mps_compatible": m2_device == "mps",
        "load_error": m2_load_err,
        "pairs": m2_results,
    }
except Exception as e:
    print(f"  FATAL: {e}")
    results["facebook/bart-large-mnli"] = {
        "model_id": model2_id,
        "fatal_error": str(e),
        "mps_compatible": False,
    }

# -------- Model 3: MoritzLaurer/deberta-v3-large-zeroshot-v2 --------
print("\n=== Model 3: MoritzLaurer/deberta-v3-large-zeroshot-v2 ===")
model3_id = "MoritzLaurer/deberta-v3-large-zeroshot-v2"
try:
    m3_results, m3_device, m3_load_err = run_zeroshot_pipeline(
        model3_id, PAIRS, device_arg
    )
    results["MoritzLaurer/deberta-v3-large-zeroshot-v2"] = {
        "model_id": model3_id,
        "device_used": m3_device,
        "mps_compatible": m3_device == "mps",
        "load_error": m3_load_err,
        "pairs": m3_results,
    }
except Exception as e:
    print(f"  FATAL: {e}")
    results["MoritzLaurer/deberta-v3-large-zeroshot-v2"] = {
        "model_id": model3_id,
        "fatal_error": str(e),
        "mps_compatible": False,
    }

# -------- Save results --------
output_path = "agents/researcher/findings/r004_nli_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n\nResults saved to {output_path}")
print("\n=== SUMMARY ===")
for model_id, res in results.items():
    if "pairs" in res:
        correct = sum(1 for p in res["pairs"] if p.get("correct", False))
        total = len([p for p in res["pairs"] if "error" not in p and "correct" in p])
        print(
            f"{model_id}: {correct}/{total} correct, device={res['device_used']}, MPS={res['mps_compatible']}"
        )
    else:
        print(f"{model_id}: FAILED — {res.get('fatal_error', 'unknown')}")
