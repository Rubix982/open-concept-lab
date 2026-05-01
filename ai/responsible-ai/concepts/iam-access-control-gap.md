# The IAM / Access Control Gap in AI

## The Core Architectural Problem

Current AI safety assumes one model for everyone:

```
ONE MODEL FOR EVERYONE
├── Contains all knowledge (good + bad)
├── Safety = behavioral guardrails only
├── Guardrails are imperfect and probeable
└── Researchers/bad actors MUST jailbreak to get sensitive data
```

The alternative — tiered models — doesn't exist at scale yet.

## The "Jailbreak As Key" Insight

> If there is one model that knows everything, jailbreaking isn't a crime —
> it's a necessity for legitimate researchers who need that knowledge.

The safety layer has no legitimate front door. Anyone who needs the locked
room has to pick the lock. The problem isn't jailbreaking.
The problem is there's no legitimate key.

## Why Cryptographic IAM Inside The Model Is Hard

Knowledge in an LLM isn't stored like a database row.
It's distributed across billions of parameters simultaneously.

```
Filing cabinet  → lock the drawer = access controlled ✓
Human brain     → try telling a doctor to forget pathogens ✗
LLMs            → closer to brain than filing cabinet
```

## Machine Unlearning — Why "Just Remove It" Fails

- Best case: 21% of target knowledge still remains after unlearning
- After quantization: 83% comes BACK
- Collateral damage: removing harmful biology damages useful biology
- Unlearning leaves fingerprints detectable from model outputs

## What Would Actually Work

1. Cryptographically partitioned neural architectures
2. Knowledge isolation during training into separable regions
3. Verifiable credential consumption air-gapped
4. Tiered model deployment (separate models, not one model with guards)

None of this exists yet.

## The Cheat Code Analogy

```
Video game cheat code  →  Privileged system prompt / jailbreak
Game developer         →  Anthropic / OpenAI
Trusted player         →  Verified researcher / doctor
Random player          →  General public
```

The AI safety problem is not really about the model.
It is about the missing key management system around it.
