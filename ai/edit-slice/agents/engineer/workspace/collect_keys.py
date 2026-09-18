"""E-016 gate · Collect layer-5 keys and measure whether whitening can matter at all.

ROME's update is `u = C⁻¹k*` where C is the second-moment matrix of MLP keys. If that
distribution is near-isotropic then C⁻¹ ∝ I, u ∝ k*, and the whitened editor is
arithmetically identical to the one [E-013]–[E-015] already ran. Measuring the spectrum
is cheap and can close E-016 without an experiment.

Keys come back fp16 and chunked; the 14336² covariance is never formed here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import load_counterfact  # noqa: E402
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-keys", type=int, default=2048)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B")
    args = ap.parse_args()

    log = setup("collect_keys", config={
        "ticket": "E-016", "gate": "anisotropy", "layer": LAYER,
        "model": args.model, "n_keys_target": args.n_keys,
        "corpus": "CounterFact prompts (NOT Wikipedia — divergence from ROME, recorded)"})

    prompts = [r.rewrite.prompt for r in load_counterfact()][:600]
    log.info("%d prompts available; targeting %d keys at layer %d",
             len(prompts), args.n_keys, LAYER)

    m = connect(args.model)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    cache = ROOT / "results" / "cache" / f"E016_keys_L{LAYER}.pt"
    chunks: list[torch.Tensor] = []
    if cache.exists():
        chunks = [torch.load(cache)]
        log.info("resumed %d keys from cache", chunks[0].shape[0])

    have = sum(c.shape[0] for c in chunks)
    i = 0
    while have < args.n_keys and i < len(prompts):
        grp = prompts[i : i + args.batch]
        i += args.batch
        ids = [tok(p).input_ids for p in grp]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        mask = torch.zeros((len(ids), width), dtype=torch.bool)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)
            mask[j, : len(x)] = True

        def once():
            with m.trace(batch, remote=True):
                k = m.model.layers[LAYER].mlp.down_proj.input
                out = k.half().save()
            return out

        got = retrying(once, what=f"key batch at {have}")
        k = got[mask].float()            # [n_real_tokens, d_mlp], padding dropped
        chunks.append(k)
        have += k.shape[0]
        torch.save(torch.cat(chunks), cache)
        chunks = [torch.load(cache)]
        log.info("  %d/%d keys", have, args.n_keys)

    K = torch.cat(chunks)[: args.n_keys]
    N, d = K.shape
    log.info("collected K: %s", tuple(K.shape))

    # Spectrum via the N x N Gram matrix — the d x d covariance (0.82 GB) is never formed.
    G = (K @ K.T) / N
    ev = torch.linalg.eigvalsh(G.double()).clamp(min=0).flip(0)
    tot = float(ev.sum())
    log.info("")
    log.info("SPECTRUM of the layer-%d key second moment (N=%d, d=%d, rank<=%d)",
             LAYER, N, d, min(N, d))
    log.info("   top eigenvalue        %.4e", ev[0])
    log.info("   median (of nonzero)   %.4e", ev[ev > 0].median())
    log.info("   smallest nonzero      %.4e", ev[ev > 0].min())
    log.info("   condition number      %.3e", ev[0] / ev[ev > 0].min())
    # participation ratio: d_eff = (sum l)^2 / sum l^2. d_eff ~ rank => isotropic.
    pr = float(tot ** 2 / (ev ** 2).sum())
    log.info("   participation ratio   %.1f  of %d sampled dims (%.2f%%)",
             pr, min(N, d), 100 * pr / min(N, d))
    for frac in (0.5, 0.9, 0.99):
        cum = torch.cumsum(ev, 0) / tot
        n_dim = int((cum < frac).sum()) + 1
        log.info("   %.0f%% of variance in %d dims (%.1f%% of sampled)",
                 100 * frac, n_dim, 100 * n_dim / min(N, d))

    log.info("")
    if pr / min(N, d) > 0.5:
        log.warning("GATE: near-isotropic — whitening is close to a no-op. "
                    "E-016 likely closes without an experiment.")
    else:
        log.info("GATE CLEARS: strongly anisotropic, so C^-1 k* is NOT proportional to "
                 "k* and the whitened editor is a materially different update.")


if __name__ == "__main__":
    main()
