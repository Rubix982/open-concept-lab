"""
R-004: NLI Model Evaluation - Standard zero-shot-classification approach
The canonical way to use these models: pass text to classify + candidate labels.
For NLI edge classification between claims A and B:
- Text = claim B (hypothesis)
- Candidate labels derived from claim A as hypothesis_template context
- OR: use MNLI label names entailment/neutral/contradiction with default template

This run uses the simplest recommended approach from HuggingFace docs:
  text = "claim_a [SEP] claim_b" framing via multi-label NLI
"""

import json
import time
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
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


def run_nli_direct_pair(model_id, pairs, device, device_label):
    """
    Directly tokenize (claim_a, claim_b) as (premise, hypothesis) and
    run through the NLI model. This is the intended usage for 3-class NLI models.
    The difference from run 2: we try BOTH orderings and report both.
    Also test with claim_a as sequence-to-classify and claim_b as premise.
    """
    model_results = []
    actual_device = device_label
    load_error = None

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(model_id)
        model = model.to(device)
        model.eval()
        print(f"  Loaded on {device_label}")
        print(f"  Label mapping: {model.config.id2label}")
    except Exception as e:
        load_error = str(e)
        print(f"  Load failed: {e}")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSequenceClassification.from_pretrained(model_id)
            model.eval()
            device = torch.device("cpu")
            actual_device = "cpu"
            print("  Loaded on CPU")
        except Exception as e2:
            return [], "failed", str(e2)

    id2label = model.config.id2label

    def normalize_label(raw_label):
        raw = raw_label.lower()
        if "entail" in raw:
            return "entailment"
        elif "contradict" in raw:
            return "contradiction"
        elif "neutral" in raw or "not_entail" in raw:
            return "neutral"
        return raw_label.lower()

    for pair in pairs:
        try:
            t0 = time.perf_counter()
            # Standard NLI: premise = claim_a, hypothesis = claim_b
            inputs = tokenizer(
                pair["claim_a"],
                pair["claim_b"],
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = model(**inputs).logits

            probs = F.softmax(logits, dim=-1).squeeze().cpu()
            elapsed = time.perf_counter() - t0

            scores = {}
            for idx, prob in enumerate(probs.tolist()):
                norm = normalize_label(id2label[idx])
                scores[norm] = round(prob, 4)

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
                    "method": "premise=claim_a, hypothesis=claim_b",
                }
            )
            marker = "OK" if predicted == pair["expected"] else "MISS"
            print(
                f"  {pair['id']} [{marker}]: {predicted} ({confidence:.3f}) in {elapsed*1000:.0f}ms [expected={pair['expected']}] | scores={scores}"
            )
        except Exception as e:
            model_results.append({"pair_id": pair["id"], "error": str(e)})
            print(f"  {pair['id']}: ERROR {e}")

    return model_results, actual_device, load_error


# Also test the zero-shot pipeline approach with the NLI template
def run_zero_shot_proper(model_id, pairs, device_label):
    """
    Use zero-shot-classification with standard template.
    The pipeline does: for each candidate label c, it checks:
    'Does [text] imply [hypothesis_template.format(c)]?'
    Standard template: "This example is {label}."
    For NLI claim classification:
    - text = claim_b
    - labels = ["supported by", "contradicted by", "unrelated to"] + context from claim_a
    """
    model_results = []
    actual_device = device_label
    load_error = None

    try:
        clf = pipeline(
            "zero-shot-classification",
            model=model_id,
            device=device_label,
        )
    except Exception as e:
        load_error = str(e)
        print(f"  Pipeline load on {device_label} failed: {e}, trying CPU...")
        try:
            clf = pipeline("zero-shot-classification", model=model_id, device="cpu")
            actual_device = "cpu"
        except Exception as e2:
            return [], "failed", str(e2)

    candidate_labels = [
        "supports the claim",
        "contradicts the claim",
        "is unrelated to the claim",
    ]
    label_map = {
        "supports the claim": "entailment",
        "contradicts the claim": "contradiction",
        "is unrelated to the claim": "neutral",
    }

    for pair in pairs:
        try:
            text = pair["claim_b"]
            # hypothesis_template: "Given claim: {premise}. The hypothesis {label}."
            template = f"Given the claim '{pair['claim_a']}', the hypothesis {{}}."
            t0 = time.perf_counter()
            out = clf(text, candidate_labels, hypothesis_template=template)
            elapsed = time.perf_counter() - t0

            raw_predicted = out["labels"][0]
            predicted = label_map[raw_predicted]
            confidence = out["scores"][0]
            all_scores = {
                label_map[l]: round(s, 4) for l, s in zip(out["labels"], out["scores"])
            }

            model_results.append(
                {
                    "pair_id": pair["id"],
                    "expected": pair["expected"],
                    "predicted": predicted,
                    "confidence": round(confidence, 4),
                    "all_scores": all_scores,
                    "inference_time_s": round(elapsed, 3),
                    "correct": predicted == pair["expected"],
                    "device_used": actual_device,
                    "method": "zero-shot-supports/contradicts/unrelated template",
                }
            )
            marker = "OK" if predicted == pair["expected"] else "MISS"
            print(
                f"  {pair['id']} [{marker}]: {predicted} ({confidence:.3f}) in {elapsed*1000:.0f}ms [expected={pair['expected']}] | {all_scores}"
            )
        except Exception as e:
            model_results.append({"pair_id": pair["id"], "error": str(e)})
            print(f"  {pair['id']}: ERROR {e}")

    return model_results, actual_device, load_error


# Load existing results
results_path = "agents/researcher/findings/r004_nli_results.json"
with open(results_path) as f:
    results = json.load(f)

# Use deberta-v3-small as it's the best candidate; test both approaches on it
model1_id = "cross-encoder/nli-deberta-v3-small"

print(f"\n=== {model1_id}: standard NLI pair (A=premise, B=hypothesis) ===")
m1a_results, m1a_device, m1a_err = run_nli_direct_pair(
    model1_id, PAIRS, device, device_label
)
results[model1_id + "_standard_pair"] = {
    "model_id": model1_id,
    "method": "A=premise,B=hypothesis direct",
    "device_used": m1a_device,
    "mps_compatible": m1a_device == "mps",
    "pairs": m1a_results,
}

print(f"\n=== {model1_id}: zero-shot supports/contradicts/unrelated template ===")
m1b_results, m1b_device, m1b_err = run_zero_shot_proper(model1_id, PAIRS, device_label)
results[model1_id + "_zeroshot_template"] = {
    "model_id": model1_id,
    "method": "zero-shot supports/contradicts/unrelated",
    "device_used": m1b_device,
    "mps_compatible": m1b_device == "mps",
    "pairs": m1b_results,
}

# Also test BART with zero-shot template (it was trained on MNLI, good for this)
model2_id = "facebook/bart-large-mnli"
print(f"\n=== {model2_id}: zero-shot supports/contradicts/unrelated template ===")
m2b_results, m2b_device, m2b_err = run_zero_shot_proper(model2_id, PAIRS, device_label)
results[model2_id + "_zeroshot_template"] = {
    "model_id": model2_id,
    "method": "zero-shot supports/contradicts/unrelated",
    "device_used": m2b_device,
    "mps_compatible": m2b_device == "mps",
    "pairs": m2b_results,
}

with open(results_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n\n=== SUMMARY (standard encoding variants) ===")
for key in [
    model1_id + "_standard_pair",
    model1_id + "_zeroshot_template",
    model2_id + "_zeroshot_template",
]:
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
            f"{res['model_id']} [{res['method']}]: {correct}/{total} correct, avg {avg_ms:.0f}ms, MPS={res['mps_compatible']}"
        )

print(f"\nSaved to {results_path}")
