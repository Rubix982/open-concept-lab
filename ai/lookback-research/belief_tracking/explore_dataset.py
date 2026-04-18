"""
Exploration of the CausalToM dataset.

Runs entirely locally — no model, no API keys needed.
Shows how stories are generated, what the belief states look like,
and what the model is actually being asked to answer.
"""

import json
import random
import sys
import os
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.dataset import Sample, Dataset

random.seed(42)


# =============================================================================
# Load entities
# =============================================================================

def load_entities(data_dir: str) -> tuple[list[str], list[str], list[str]]:
    characters: list[str] = json.load(open(f"{data_dir}/synthetic_entities/characters.json"))
    objects:    list[str] = json.load(open(f"{data_dir}/synthetic_entities/bottles.json"))
    states:     list[str] = json.load(open(f"{data_dir}/synthetic_entities/drinks.json"))
    return characters, objects, states

data_dir = os.path.join(os.path.dirname(__file__), "data")
characters, objects, states = load_entities(data_dir)

print("=" * 60)
print("AVAILABLE ENTITIES")
print("=" * 60)
print(f"  Characters ({len(characters)}): {characters[:8]} ...")
print(f"  Objects    ({len(objects)}):    {objects[:8]} ...")
print(f"  States     ({len(states)}):     {states[:8]} ...")


# =============================================================================
# The 4 story templates — what varies between them
# =============================================================================

print("\n" + "=" * 60)
print("THE 4 STORY TEMPLATES")
print("=" * 60)

templates: dict[str, Any] = json.load(open(f"{data_dir}/story_templates.json"))
for i, t in enumerate(templates["templates"]):
    print(f"\n  Template {i}:")
    print(f"  {t['context'][:120]}...")

print("""
  Template 0: neither character observes the other (no visibility)
  Template 1: char1 CAN observe char2 (one-way visibility)
  Template 2: no explicit visibility statement
  Template 3: different characters named in visibility (distractors)
""")


# =============================================================================
# Generate samples across all templates and show what they look like
# =============================================================================

print("=" * 60)
print("GENERATED SAMPLES — one per template")
print("=" * 60)

dataset_samples: list[Sample] = []

for template_idx in range(4):
    n_chars = 4 if template_idx == 3 else 2   # template 3 uses 4 character placeholders
    chars   = random.sample(characters, n_chars)
    objs    = random.sample(objects, 2)
    sts     = random.sample(states, 2)
    sample  = Sample(
        template_idx=template_idx,
        characters=chars,
        objects=objs,
        states=sts,
    )
    dataset_samples.append(sample)

    print(f"\n--- Template {template_idx} ---")
    print(f"  Story:\n    {sample.story}")
    print(f"  World state (ground truth): {sample.world_state}")
    print(f"  {chars[0]}'s beliefs:        {sample.character_belief[0]}")
    print(f"  {chars[1]}'s beliefs:        {sample.character_belief[1]}")


# =============================================================================
# Show the full prompt the model receives — exactly what goes into the LLM
# =============================================================================

print("\n" + "=" * 60)
print("FULL PROMPT SENT TO THE MODEL (Template 0 — no visibility)")
print("=" * 60)

ds = Dataset(samples=[dataset_samples[0]])

# Ask about char1's belief about obj2 — the hard case (they didn't observe each other)
prompt_data: dict[str, Any] = ds.__getitem__(0, set_character=0, set_container=1)
print(prompt_data["prompt"])
print(f"  Expected answer: '{prompt_data['target']}'")


# =============================================================================
# Show counterfactual pairs — the key to causal mediation
# =============================================================================

print("\n" + "=" * 60)
print("COUNTERFACTUAL PAIRS — how causal mediation works")
print("=" * 60)

print("""
  For causal mediation, you need pairs of stories that differ in one
  specific way so you can patch activations between them.

  Example pair for tracing Character1 OI:
""")

chars_a = ["Dean", "Beth"]
chars_b = ["Jake", "Karen"]   # different characters, same structure
obj_pair = random.sample(objects, 2)
st_pair  = random.sample(states, 2)

sample_a = Sample(template_idx=0, characters=chars_a, objects=obj_pair, states=st_pair)
sample_b = Sample(template_idx=0, characters=chars_b, objects=obj_pair, states=st_pair)

print(f"  Story A: {sample_a.story[:100]}...")
print(f"  Story B: {sample_b.story[:100]}...")
print(f"""
  Causal mediation experiment:
    1. Run model on Story A → correct answer
    2. Run model on Story B → correct answer
    3. Patch Story A's run with Story B's activation at (layer L, token T)
    4. If output changes → that (layer, token) carries the character OI

  The dataset generator creates these pairs systematically for every
  (character, object, state) combination across all templates.
""")


# =============================================================================
# Belief state summary across templates
# =============================================================================

print("=" * 60)
print("BELIEF STATE MATRIX — what each template tests")
print("=" * 60)

print("""
  Template | char1 knows obj1 | char1 knows obj2 | char2 knows obj1 | char2 knows obj2
  ---------|------------------|------------------|------------------|------------------
     0     |       YES        |       NO         |       NO         |       YES
     1     |       YES        |       YES        |       NO         |       YES
     2     |       YES        |    ambiguous     |    ambiguous     |       YES
     3     |       YES        |       NO         |       NO         |       YES

  Template 1 is the visibility case — char1 observed char2, so char1
  knows what char2 did. That's the visibility lookback scenario.
  Template 0 is the pure no-visibility baseline.
""")
