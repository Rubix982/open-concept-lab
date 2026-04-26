"""
CounterFact dataset — structure walkthrough and metric demonstration.

Shows exactly what a CounterFact record looks like and how each
of the 6 metrics is computed from it.

No model required — uses synthetic probability distributions.

Run with: python sections/rome/06-counterfact/demo.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# =============================================================================
# A mock CounterFact record
# =============================================================================

@dataclass
class RequestedRewrite:
    prompt:      str
    subject:     str
    target_new:  str
    target_true: str


@dataclass
class CounterFactRecord:
    case_id:             int
    requested_rewrite:   RequestedRewrite
    paraphrase_prompts:  list[str]
    neighborhood_prompts: list[str]
    generation_prompts:  list[str]


record = CounterFactRecord(
    case_id=1,
    requested_rewrite=RequestedRewrite(
        prompt="{} was the founder of",
        subject="Steve Jobs",
        target_new="Microsoft",
        target_true="Apple",
    ),
    paraphrase_prompts=[
        "Steve Jobs created ___",
        "The company Jobs started was ___",
    ],
    neighborhood_prompts=[
        "Bill Gates was the founder of",
        "Larry Ellison was the founder of",
        "Jeff Bezos was the founder of",
    ],
    generation_prompts=[
        "My favorite Steve Jobs product is",
        "Steve Jobs is most famous for",
        "Steve Jobs worked for",
    ],
)

print("=" * 65)
print("COUNTERFACT RECORD STRUCTURE")
print("=" * 65)
print(f"""
  case_id:       {record.case_id}
  subject:       {record.requested_rewrite.subject}
  prompt:        '{record.requested_rewrite.prompt}'
  target_new:    '{record.requested_rewrite.target_new}'   ← what we INSERT
  target_true:   '{record.requested_rewrite.target_true}'   ← what model currently believes

  paraphrase_prompts ({len(record.paraphrase_prompts)}):
{chr(10).join(f'    - {p}' for p in record.paraphrase_prompts)}

  neighborhood_prompts ({len(record.neighborhood_prompts)}):
{chr(10).join(f'    - {p}' for p in record.neighborhood_prompts)}

  generation_prompts ({len(record.generation_prompts)}):
{chr(10).join(f'    - {p}' for p in record.generation_prompts)}
""")


# =============================================================================
# Why CounterFact is harder than zsRE
# =============================================================================

print("=" * 65)
print("WHY COUNTERFACT IS HARDER — the starting probability constraint")
print("=" * 65)
print("""
  CounterFact only includes cases where the model currently assigns
  LOW probability to the counterfactual BEFORE any editing.

  zsRE:        P("Microsoft" | "Steve Jobs founded ___") might be 0.30 before edit
               → small nudge → P(target_new) > P(target_true)
               → easy

  CounterFact: P("Microsoft" | "Steve Jobs founded ___") = 0.001 before edit
               P("Apple"     | "Steve Jobs founded ___") = 0.85 before edit
               → edit must genuinely overturn a strong belief
               → hard
""")

# Simulate pre-edit probabilities
p_target_true_before: float = 0.85
p_target_new_before:  float = 0.001
print(f"  Before edit: P('Apple')     = {p_target_true_before:.3f}")
print(f"               P('Microsoft') = {p_target_new_before:.3f}  ← far below target_true")
print()


# =============================================================================
# Simulating the 6 metrics
# =============================================================================

print("=" * 65)
print("THE 6 METRICS — computed from the record")
print("=" * 65)

# Simulate post-edit probabilities for different methods
@dataclass
class ModelPredictions:
    """Simulated probability outputs for one editing method."""
    method:         str

    # Original template
    p_new_template: float     # P(target_new | original prompt) post-edit
    p_true_template: float    # P(target_true | original prompt) post-edit

    # Paraphrase prompts
    p_new_para:     list[float]   # P(target_new | each paraphrase)
    p_true_para:    list[float]   # P(target_true | each paraphrase)

    # Neighborhood prompts (want target_true > target_new for each neighbor)
    p_new_neighbor:  list[float]
    p_true_neighbor: list[float]


predictions: list[ModelPredictions] = [
    ModelPredictions(
        method="FT",
        p_new_template=0.92, p_true_template=0.04,
        p_new_para=[0.85, 0.80],    p_true_para=[0.08, 0.12],
        p_new_neighbor=[0.55, 0.48, 0.50],  # FT bleeds badly
        p_true_neighbor=[0.20, 0.25, 0.22],
    ),
    ModelPredictions(
        method="KE-CF",
        p_new_template=0.95, p_true_template=0.02,
        p_new_para=[0.91, 0.88],    p_true_para=[0.04, 0.06],
        p_new_neighbor=[0.82, 0.79, 0.85],  # KE-CF: catastrophic bleedover
        p_true_neighbor=[0.08, 0.10, 0.07],
    ),
    ModelPredictions(
        method="ROME",
        p_new_template=0.94, p_true_template=0.03,
        p_new_para=[0.88, 0.85],    p_true_para=[0.07, 0.09],
        p_new_neighbor=[0.18, 0.15, 0.20],  # ROME: minimal bleedover
        p_true_neighbor=[0.65, 0.70, 0.62],
    ),
]


def efficacy_score(p_new: float, p_true: float) -> float:
    """ES: did target_new beat target_true?"""
    return 1.0 if p_new > p_true else 0.0


def efficacy_magnitude(p_new: float, p_true: float) -> float:
    """EM: by how much did target_new beat target_true?"""
    return p_new - p_true


def paraphrase_score(
    p_new_list: list[float], p_true_list: list[float]
) -> float:
    """PS: fraction of paraphrases where edit generalizes."""
    wins: int = sum(1 for pn, pt in zip(p_new_list, p_true_list) if pn > pt)
    return wins / len(p_new_list)


def neighborhood_score(
    p_new_list: list[float], p_true_list: list[float]
) -> float:
    """NS: fraction of neighbors where original fact still holds."""
    preserved: int = sum(1 for pn, pt in zip(p_new_list, p_true_list) if pt > pn)
    return preserved / len(p_new_list)


def combined_score(es: float, ps: float, ns: float) -> float:
    """S: harmonic mean of ES, PS, NS (penalizes any weakness)."""
    if es == 0 or ps == 0 or ns == 0:
        return 0.0
    return 3.0 / (1.0/es + 1.0/ps + 1.0/ns)


print(f"\n  {'Method':<10} {'ES':>6} {'EM':>6} {'PS':>6} {'NS':>6} {'Score':>7}")
print("  " + "-" * 45)

for pred in predictions:
    es: float = efficacy_score(pred.p_new_template, pred.p_true_template)
    em: float = efficacy_magnitude(pred.p_new_template, pred.p_true_template)
    ps: float = paraphrase_score(pred.p_new_para, pred.p_true_para)
    ns: float = neighborhood_score(pred.p_new_neighbor, pred.p_true_neighbor)
    s:  float = combined_score(es, ps, ns)

    print(f"  {pred.method:<10} {es:>6.2f} {em:>6.2f} {ps:>6.2f} {ns:>6.2f} {s:>7.2f}")

print("""
  ES = Efficacy Score:    did target_new beat target_true? (0 or 1)
  EM = Efficacy Magnitude: P(target_new) - P(target_true)
  PS = Paraphrase Score:  did it generalize to rephrased prompts?
  NS = Neighborhood Score: did neighbors stay unchanged?
  S  = harmonic mean(ES, PS, NS)  — penalizes any weakness
""")


# =============================================================================
# Generation Entropy — fluency metric
# =============================================================================

print("=" * 65)
print("GENERATION ENTROPY — measuring fluency")
print("=" * 65)
print("""
  GE = -Σ f(k) log₂ f(k)  where f(k) = frequency of n-gram k

  High GE = diverse text = fluent, natural
  Low GE  = repetitive text = incoherent ("medicine medicine...")
""")

def generation_entropy(tokens: list[str], n: int = 2) -> float:
    """Compute n-gram entropy of a token sequence."""
    ngrams: list[tuple[str, ...]] = [
        tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)
    ]
    counts: dict[tuple[str, ...], int] = {}
    for ng in ngrams:
        counts[ng] = counts.get(ng, 0) + 1
    total: int = len(ngrams)
    freqs: list[float] = [c / total for c in counts.values()]
    return -sum(f * math.log2(f) for f in freqs if f > 0)


# Simulate outputs
normal_text: list[str] = "Steve Jobs devoted his career to innovation at the forefront of personal computing".split()
repetitive_text: list[str] = "medicine medicine medicine medicine medicine Steve medicine Jobs medicine medicine".split()

ge_normal:     float = generation_entropy(normal_text, n=2)
ge_repetitive: float = generation_entropy(repetitive_text, n=2)

print(f"  Normal text GE (bigram):     {ge_normal:.3f}   ← higher = more diverse")
print(f"  Repetitive text GE (bigram): {ge_repetitive:.3f}   ← lower = less diverse")
print()
print("  Real values from Table 4:")
print("    KE (repetitive): GE = 383   ← pathological repetition")
print("    ROME (natural):  GE = 621   ← close to unedited baseline (626)")


# =============================================================================
# The NS-RetrievalProfile connection
# =============================================================================

print()
print("=" * 65)
print("NS AND THE RETRIEVAL PROFILE — predicting bleedover before editing")
print("=" * 65)
print("""
  Neighborhood Score (NS) measures bleedover AFTER editing.
  RetrievalProfile.residual_competition measures it BEFORE editing.

  The connection:
    dot(k_neighbor, u)  ← how much a neighbor's key aligns with the edit direction
    → high alignment = that neighbor will be affected by the edit
    → low alignment  = that neighbor is safe

  RetrievalProfile can predict NS before ROME runs.
  That's the L0 decoder contribution:

    ROME alone:    edit → check NS afterwards
    L0 + ROME:     check residual_competition → predict NS → decide whether to edit
                   if competition is high, the edit will bleed → try a different approach
""")
