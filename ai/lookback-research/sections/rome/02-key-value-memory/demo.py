"""
compute_u and compute_v — toy demonstration.

No model required. Uses small readable matrices to show exactly
what each function computes and how the rank-one update works.

Run with: python sections/rome/02-key-value-memory/demo.py
"""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

# =============================================================================
# Toy MLP weight matrix (the "phone book")
# =============================================================================
#
# In GPT-2 XL: W_proj is (1600 × 6400)
# Here we use (4 × 6) for readability — same structure, tiny size.
#
# W maps a 6D key → 4D value
# Think: W[subject_representation] ≈ object_representation

np.random.seed(42)
D_MODEL = 4   # output dimension (d_model)
D_MLP   = 6   # input dimension  (d_mlp = 4 × d_model in real GPT)

W = np.random.randn(D_MODEL, D_MLP) * 0.3
print("=" * 60)
print("Original MLP weight matrix W  (shape: D_MODEL × D_MLP)")
print("=" * 60)
print(np.round(W, 3))
print()


# =============================================================================
# The factual association we want to edit
# =============================================================================

# Before edit: "Steve Jobs" → W @ k_jobs ≈ v_apple
# After edit:  "Steve Jobs" → W @ k_jobs ≈ v_microsoft

# Subject key: the hidden state at "Jobs" token, layer 17 MLP input
k_subject = np.array([0.8, 0.3, -0.5, 0.9, 0.1, -0.2])   # 6D

# Current output: what W produces for this key (approximates "Apple")
v_current = W @ k_subject
print("=" * 60)
print("Current MLP output for 'Steve Jobs' key")
print("= W @ k_subject  (approximates Apple representation)")
print("=" * 60)
print(np.round(v_current, 3))
print()


# =============================================================================
# STEP 1: compute_u — the key direction (C⁻¹k*)
# =============================================================================
#
# In the real code: C = KKᵀ = covariance of 100k Wikipedia key vectors
# Here: simulate C as a small SPD matrix

print("=" * 60)
print("STEP 1: compute_u — find the key direction")
print("=" * 60)

# Simulate the covariance matrix C = KKᵀ
# (in practice: computed from 100k Wikipedia sentences)
random_keys = np.random.randn(D_MLP, 200)   # 200 Wikipedia "keys"
C = random_keys @ random_keys.T / 200        # uncentered covariance
C_inv = np.linalg.inv(C + 1e-4 * np.eye(D_MLP))  # inverse (+ small regularizer)

print("C (covariance of Wikipedia keys):")
print(np.round(C, 2))
print()
print("C_inv (inverse covariance):")
print(np.round(C_inv, 2))
print()

# Apply inverse covariance: u = C⁻¹ @ k*
u_raw = C_inv @ k_subject
u = u_raw / np.linalg.norm(u_raw)   # normalize to unit vector

print("k_subject (raw subject representation):")
print(np.round(k_subject, 3))
print()
print("u = C⁻¹ @ k_subject  (whitened, normalized):")
print(np.round(u, 3))
print()
print("Why whitening matters:")
print(f"  Raw k_subject norm:  {np.linalg.norm(k_subject):.3f}")
print(f"  u norm (after):      {np.linalg.norm(u):.3f}  ← unit vector")
print(f"  Direction changed:   cosine similarity = {np.dot(k_subject/np.linalg.norm(k_subject), u):.3f}")
print(f"  (not 1.0 — C⁻¹ rotated it to a more specific direction)")
print()


# =============================================================================
# STEP 2: compute_v — the value delta (optimization)
# =============================================================================
#
# Goal: find v* such that W @ k_subject ≈ v*
#       and v* causes the model to predict "Microsoft"
#
# In the real code: run 20 steps of Adam
# Here: simulate by directly specifying the target and computing delta

print("=" * 60)
print("STEP 2: compute_v — find the value delta")
print("=" * 60)

# The desired new output (what "Microsoft" looks like as an MLP output)
# In the real code this is found by optimization
# Here: simulate as a shifted version of v_current
v_target = np.array([0.9, -0.7, 0.4, -0.8])   # 4D — "Microsoft" representation
delta = v_target - v_current

print("v_current (what W currently outputs for Steve Jobs):")
print(np.round(v_current, 3))
print()
print("v_target  (desired output — encodes 'Microsoft'):")
print(np.round(v_target, 3))
print()
print("delta = v_target - v_current:")
print(np.round(delta, 3))
print(f"delta norm: {np.linalg.norm(delta):.3f}")
print()

# Simulating the three loss terms at each optimization step
print("Simulating optimization (real code runs 20 Adam steps):")
print(f"  Step 0:  loss = nll_high + kl=0.0 + wd=0.0  | prob(Microsoft)=0.001")
print(f"  Step 5:  loss = nll_med  + kl=0.001 + wd=0.04| prob(Microsoft)=0.456")
print(f"  Step 20: loss = nll_low  + kl=0.005 + wd=0.097| prob(Microsoft)=0.980")
print()
print("The three loss terms and what they protect:")
print("  nll_loss:    maximize P('Microsoft' | 'Steve Jobs founded ___')")
print("  kl_loss:     keep P('Steve Jobs is a ___') unchanged  [essence drift]")
print("  weight_decay: keep delta small  [minimal surgical change]")
print()


# =============================================================================
# STEP 3: Compute the right vector (Λ)
# =============================================================================
#
# From the paper: Λ = (v* - Wk*) / (C⁻¹k*)ᵀk*
# In code: right_vector = (target - cur_output) / dot(cur_input, left_vector)

print("=" * 60)
print("STEP 3: Compute right vector Λ (the rank-one column)")
print("=" * 60)

numerator   = v_target - v_current          # (v* - Wk*)
denominator = np.dot(k_subject, u)          # (C⁻¹k*)ᵀk*  [scalar]
Lambda      = numerator / denominator       # Λ

print(f"numerator  = v_target - v_current:")
print(f"  {np.round(numerator, 3)}")
print(f"denominator = dot(k_subject, u) = {denominator:.4f}  [scalar]")
print(f"Λ = numerator / denominator:")
print(f"  {np.round(Lambda, 3)}")
print()


# =============================================================================
# STEP 4: Apply the rank-one update
# =============================================================================
#
# W_new = W + Λ @ u.T   (outer product — same shape as W)

print("=" * 60)
print("STEP 4: Apply rank-one update  W_new = W + outer_product(Λ, u)")
print("=" * 60)

rank_one_update = np.outer(Lambda, u)      # (D_MODEL × D_MLP)
W_new = W + rank_one_update

print("Rank-one update matrix  outer_product(Λ, u):")
print(np.round(rank_one_update, 3))
print()
print("W_new = W + rank_one_update:")
print(np.round(W_new, 3))
print()


# =============================================================================
# VERIFY: does W_new @ k_subject ≈ v_target?
# =============================================================================

print("=" * 60)
print("VERIFICATION")
print("=" * 60)

v_before = W     @ k_subject
v_after  = W_new @ k_subject

print(f"W_old     @ k_subject = {np.round(v_before, 3)}  (original output)")
print(f"W_new     @ k_subject = {np.round(v_after,  3)}  (after edit)")
print(f"v_target              = {np.round(v_target,  3)}  (desired output)")
print()
print(f"Edit error (||W_new @ k - v_target||): {np.linalg.norm(v_after - v_target):.6f}")
print(f"  {'✓ Nearly zero — edit succeeded!' if np.linalg.norm(v_after - v_target) < 1e-8 else '(small error due to floating point)'}")
print()


# =============================================================================
# SPECIFICITY CHECK: does a different subject change?
# =============================================================================

print("=" * 60)
print("SPECIFICITY CHECK — does the edit affect other subjects?")
print("=" * 60)

k_other = np.array([0.1, 0.9, 0.2, -0.1, 0.7, 0.3])   # "Bill Gates" representation

v_other_before = W     @ k_other
v_other_after  = W_new @ k_other
change = np.linalg.norm(v_other_after - v_other_before)

print(f"'Bill Gates' key:          {np.round(k_other, 3)}")
print(f"Output before edit:        {np.round(v_other_before, 3)}")
print(f"Output after edit:         {np.round(v_other_after, 3)}")
print(f"Change magnitude:          {change:.4f}")
print()
print(f"Why it's small: u is whitened by C⁻¹, making it nearly orthogonal")
print(f"to common key directions. Other subjects are unaffected because their")
print(f"k doesn't align with u.")
print(f"  dot(k_other, u) = {np.dot(k_other, u):.4f}  (small → minimal projection)")
print(f"  dot(k_subject, u) = {np.dot(k_subject, u):.4f}  (larger → subject is targeted)")
print()


# =============================================================================
# SUMMARY
# =============================================================================

print("=" * 60)
print("SUMMARY: The complete ROME edit in 4 lines")
print("=" * 60)
print("""
  u       = normalize(C_inv @ k_subject)       # compute_u
  v*      = optimize(model, target="Microsoft") # compute_v (simplified)
  Lambda  = (v* - W @ k_subject) / dot(k_subject, u)  # right vector
  W_new   = W + outer_product(Lambda, u)        # rank-one update

  Result: W_new @ k_subject ≈ v*   (edit applied)
          W_new @ k_other   ≈ W @ k_other  (other facts unchanged)
""")
