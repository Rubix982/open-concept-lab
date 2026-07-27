"""
08 — Readout vs Storage: combining the logit lens (01) and the residual
     stream evolution (02) on one layer axis.

Two curves, measured at two DIFFERENT token positions, plotted against depth:

  READOUT   : P('Paris') via logit lens at the LAST token ("of").
              Where the answer surfaces into the prediction.  (from script 01)

  STORAGE   : RELATIVE change of the residual stream at the SUBJECT token
              ("Tower"), i.e. ||h_L - h_{L-1}|| / ||h_{L-1}||.
              Where the subject's representation is being rewritten. (from 02,
              but using the relative metric — raw ||Δ|| is confounded by the
              residual stream's norm growing ~7x with depth).

Reading the two together shows the handoff: the subject token is worked on in
the earlier-mid layers, and that information then surfaces as 'Paris' at the
last token slightly later.
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = 28

paris_id = model.tokenizer.encode(" Paris")[0]
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
subj_pos = max(i for i, t in enumerate(tokens) if "Tower" in t)
print(f"Tokens        : {tokens}")
print(f"Subject token : idx {subj_pos} = {tokens[subj_pos]!r}")
print(f"Answer token  : ' Paris' (id {paris_id})\n")

# one trace, everything stacked into single saved tensors (nnsight 0.7 pattern)
readout_p_list = []     # P(Paris) at last token, per layer (logit lens)
subj_vec_list = []      # subject-token residual vector, per layer

with model.trace(prompt, remote=True):
    for L in range(n_layers):
        # READOUT: logit lens at the LAST token
        resid_last = model.transformer.h[L].output[0][0, -1]     # [4096]
        logits_last = model.lm_head(model.transformer.ln_f(resid_last))
        readout_p_list.append(logits_last.softmax(dim=-1)[paris_id])

        # STORAGE: subject-token residual vector (relative change computed later)
        subj_vec_list.append(model.transformer.h[L].output[0][0, subj_pos])

    readout_p = torch.stack(readout_p_list).save()    # [28]
    subj_vecs = torch.stack(subj_vec_list).save()     # [28, 4096]

print(f"[debug] readout_p {tuple(readout_p.shape)}  subj_vecs {tuple(subj_vecs.shape)}\n")

# relative change at the subject token
rel_change = [0.0]
for L in range(1, n_layers):
    d = float((subj_vecs[L] - subj_vecs[L - 1]).norm())
    rel_change.append(d / float(subj_vecs[L - 1].norm()))

# ── combined table ─────────────────────────────────────────────────────────
print(f"{'layer':>5}  {'readout P(Paris)':>16}  {'subj rel-change':>16}")
print("─" * 44)
for L in range(n_layers):
    p = float(readout_p[L])
    bar = "█" * int(p * 20)
    print(f"{L:>5}  {p:>16.4f}  {rel_change[L]:>16.4f}  {bar}")

# ── optional plot (skipped cleanly if matplotlib is unavailable) ───────────
try:
    import matplotlib.pyplot as plt
    fig, ax1 = plt.subplots(figsize=(10, 5), facecolor="#0a0c0f")
    ax1.set_facecolor("#0f1318")
    layers = list(range(n_layers))

    ax1.plot(layers, [float(readout_p[L]) for L in layers],
             color="#4fc3f7", linewidth=2.4, marker="o", markersize=4,
             label="readout: P(Paris) @ last token")
    ax1.set_xlabel("layer", color="#c8d4e0")
    ax1.set_ylabel("P(Paris) — readout", color="#4fc3f7")
    ax1.tick_params(colors="#4a5568")

    ax2 = ax1.twinx()
    ax2.plot(layers, rel_change,
             color="#e57373", linewidth=2.0, marker="s", markersize=3,
             linestyle="--", label="storage: subj-token relative change")
    ax2.set_ylabel("relative change — storage", color="#e57373")
    ax2.tick_params(colors="#4a5568")

    for sp in ax1.spines.values(): sp.set_color("#1e2530")
    for sp in ax2.spines.values(): sp.set_color("#1e2530")
    ax1.set_title("Readout vs Storage across layers — GPT-J, Eiffel Tower → Paris",
                  color="#c8d4e0")
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88),
               facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    out = "08_readout_vs_storage.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nPlot saved → {out}")
except ImportError:
    print("\n(matplotlib not installed — skipping plot, table above is complete)")
