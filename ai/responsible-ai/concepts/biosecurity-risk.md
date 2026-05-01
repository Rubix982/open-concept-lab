# AI & Biosecurity Risk

## Why Biosecurity Is The Highest-Stakes Domain

Sam Altman (2026):
> "If something goes visibly really wrong for AI this year, I think bio would
> be a reasonable bet for what that could be."

> "There are incredibly capable open-source models that are very good at
> biology — the need for society to be resilient to terrorist groups using
> these models to try to create novel pathogens is no longer a theoretical thing."

## The Threat Model

```
Step 1: Download open-source model (Llama, Mistral) — legal, free
Step 2: Strip safety fine-tuning — documented, tools exist
Step 3: Fine-tune on PubMed, bioRxiv, virology journals — all public
Step 4: Run locally, air-gapped — no API, no logs, no oversight
```

No jailbreaking needed when you own the weights.

## The "Uplift" Concept

AI doesn't need to fully design a bioweapon. It provides:
- Filling knowledge gaps a non-expert has
- Suggesting workarounds when experiments fail
- Accelerating trial-and-error that previously required years of expertise

## The Dual-Use Core

The same knowledge that trains vaccine researchers trains bad actors.
There is no version of biology knowledge that is safe for some and dangerous
for others. The knowledge is neutral. Intent differs. Models cannot see intent.

## What's Being Done

| Defense | Limitation |
|---|---|
| API safety filters | Irrelevant for local open-source models |
| DNA synthesis screening | Only catches known sequences |
| Lab equipment export controls | Black markets exist |
| Intelligence monitoring | Cannot monitor every private compute cluster |
| Publishing restrictions | Most dangerous knowledge already public |

## The Open Source Problem

Even if Anthropic and OpenAI solve this perfectly:
- Meta releases Llama weights publicly
- Mistral releases weights publicly
- Chinese labs release weights publicly

No single country can solve this unilaterally.

## GPT-5.2 Benchmark

Scored 92% on GPQA — PhD-level biology, chemistry, physics questions
written specifically to be "Google-proof." The knowledge is already inside
these models.
