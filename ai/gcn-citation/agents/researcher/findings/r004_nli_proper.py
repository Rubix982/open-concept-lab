"""
R-004: NLI Model Evaluation - Proper premise/hypothesis pair approach
Uses text-classification with direct tokenization of [premise, hypothesis] pairs.
This is the correct way to use cross-encoder NLI models.
"""

import json
import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

# Device setup
if torch.backends.mps.is_available():
    device = torch.device("mps")
    device_label = "mps"
    print("Using MPS")
else:
    device = torch.device("cpu")
    device_label = "cpu"
    print("Using CPU")

PAIRS = [
    {
        "id": "pair1",
        "expected": "entailment",
        "label": "known_support",
        "premise": "Transformer models with multi-head self-attention outperform LSTM-based models on long-range sequence modeling tasks.",
        "hypothesis": "Self-attention mechanisms enable transformers to capture dependencies across arbitrary sequence lengths, unlike recurrent architectures.",
    },
    {
        "id": "pair2",
        "expected": "contradiction",
        "label": "known_contradiction",
        "premise": "Batch normalization consistently improves training stability and generalization across deep neural network architectures.",
        "hypothesis": "Batch normalization can degrade performance when batch size is small, and layer normalization is preferred in transformer architectures.",
    },
    {
        "id": "pair3",
        "expected": "neutral",
        "label": "known_neutral",
        "premise": "Graph neural networks aggregate neighbor features using message passing to learn node representations.",
        "hypothesis": "Diffusion probabilistic models generate images by reversing a learned noising process.",
    },
]


def run_nli_model(model_id, pairs, device, device_label):
    """
    Load model and tokenizer directly, feed (premise, hypothesis) pairs
    as token pairs — the standard NLI encoding.
    Returns list of per-pair results.
    """
    model_results = []
    load_error = None
    actual_device = device_label

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(model_id)
        model = model.to(device)
        model.eval()
        print(f"  Loaded on {device_label}")
    except Exception as e:
        load_error = str(e)
        print(f"  Load on {device_label} failed: {e}")
        # CPU fallback
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSequenceClassification.from_pretrained(model_id)
            model = model.cpu()
            model.eval()
            device = torch.device("cpu")
            actual_device = "cpu"
            print(f"  Loaded on CPU (fallback)")
        except Exception as e2:
            print(f"  FATAL on CPU: {e2}")
            return model_results, "failed", str(e2)

    # Inspect label mapping
    id2label = model.config.id2label
    print(f"  Label mapping: {id2label}")

    # Normalize label names to standard NLI names
    # DeBERTa models: {0: 'entailment', 1: 'neutral', 2: 'contradiction'} or similar
    # BART: {0: 'contradiction', 1: 'neutral', 2: 'entailment'}
    def normalize_label(raw_label):
        raw = raw_label.lower()
        if "entail" in raw:
            return "entailment"
        elif "contradict" in raw:
            return "contradiction"
        elif "neutral" in raw:
            return "neutral"
        return raw_label

    for pair in pairs:
        try:
            t0 = time.perf_counter()
            inputs = tokenizer(
                pair["premise"],
                pair["hypothesis"],
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            logits = outputs.logits
            probs = F.softmax(logits, dim=-1).squeeze().cpu()
            elapsed = time.perf_counter() - t0

            # Build score dict with normalized labels
            scores = {}
            for idx, prob in enumerate(probs.tolist()):
                raw_label = id2label[idx]
                norm_label = normalize_label(raw_label)
                scores[norm_label] = round(prob, 4)

            predicted = max(scores, key=scores.get)
            confidence = scores[predicted]

            model_results.append(
                {
                    "pair_id": pair["id"],
                    "expected": pair["expected"],
                    "predicted": predicted,
                    "confidence": confidence,
                    "all_scores": scores,
                    "inference_time_s": round(elapsed, 3),
                    "correct": predicted == pair["expected"],
                    "device_used": actual_device,
                }
            )
            marker = "OK" if predicted == pair["expected"] else "MISS"
            print(
                f"  {pair['id']} [{marker}]: predicted={predicted} (conf={confidence:.3f}) in {elapsed:.2f}s [expected={pair['expected']}]"
            )
        except Exception as e:
            model_results.append(
                {
                    "pair_id": pair["id"],
                    "expected": pair["expected"],
                    "error": str(e),
                    "device_used": actual_device,
                }
            )
            print(f"  {pair['id']}: ERROR {e}")

    return model_results, actual_device, load_error


# Load existing results
results_path = "agents/researcher/findings/r004_nli_results.json"
with open(results_path) as f:
    results = json.load(f)

# -------- Model 1: cross-encoder/nli-deberta-v3-small --------
model1_id = "cross-encoder/nli-deberta-v3-small"
print(f"\n=== Model 1: {model1_id} ===")
m1_results, m1_device, m1_err = run_nli_model(model1_id, PAIRS, device, device_label)
results[model1_id + "_proper"] = {
    "model_id": model1_id,
    "method": "direct_tokenization",
    "device_used": m1_device,
    "mps_compatible": m1_device == "mps",
    "load_error": m1_err,
    "pairs": m1_results,
}

# -------- Model 2: facebook/bart-large-mnli --------
model2_id = "facebook/bart-large-mnli"
print(f"\n=== Model 2: {model2_id} ===")
m2_results, m2_device, m2_err = run_nli_model(model2_id, PAIRS, device, device_label)
results[model2_id + "_proper"] = {
    "model_id": model2_id,
    "method": "direct_tokenization",
    "device_used": m2_device,
    "mps_compatible": m2_device == "mps",
    "load_error": m2_err,
    "pairs": m2_results,
}

# -------- Model 3: MoritzLaurer/deberta-v3-large-zeroshot-v2.0 --------
model3_id = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
print(f"\n=== Model 3: {model3_id} ===")
m3_results, m3_device, m3_err = run_nli_model(model3_id, PAIRS, device, device_label)
results[model3_id + "_proper"] = {
    "model_id": model3_id,
    "method": "direct_tokenization",
    "device_used": m3_device,
    "mps_compatible": m3_device == "mps",
    "load_error": m3_err,
    "pairs": m3_results,
}

with open(results_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n\n=== FINAL SUMMARY (proper NLI encoding) ===")
for key in [model1_id + "_proper", model2_id + "_proper", model3_id + "_proper"]:
    res = results[key]
    if "pairs" in res:
        correct = sum(1 for p in res["pairs"] if p.get("correct", False))
        total = len([p for p in res["pairs"] if "correct" in p])
        times = [
            p.get("inference_time_s", 0)
            for p in res["pairs"]
            if "inference_time_s" in p
        ]
        avg_ms = (sum(times) / len(times) * 1000) if times else 0
        print(
            f"{res['model_id']}: {correct}/{total} correct, avg {avg_ms:.0f}ms/pair, device={res['device_used']}, MPS={res['mps_compatible']}"
        )
    else:
        print(f"{res['model_id']}: FAILED")

print(f"\nSaved to {results_path}")
