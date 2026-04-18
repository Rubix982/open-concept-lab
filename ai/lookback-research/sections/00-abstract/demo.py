"""
Abstract concepts — minimal Python demos.

No ML libraries needed. These express the *logic* of each concept.
"""

# =============================================================================
# 1. Theory of Mind: belief tracking vs. ground truth
# =============================================================================

def build_world(actions):
    """Ground truth: what actually happened."""
    world = {}
    for character, obj, state in actions:
        world[obj] = state
    return world

def build_beliefs(actions, visibility):
    """
    Each character's belief state.
    visibility: dict of {observer: observed} — who saw whose action.
    """
    beliefs = {char: {} for char, _, _ in actions}

    for character, obj, state in actions:
        # A character always knows their own action
        beliefs[character][obj] = state

    # Apply visibility: if A observed B, A knows what B did
    for observer, observed in visibility.items():
        for character, obj, state in actions:
            if character == observed:
                beliefs[observer][obj] = state

    return beliefs

actions = [
    ("Bob",   "bottle", "beer"),
    ("Carla", "cup",    "coffee"),
]

# No visibility: each character only knows their own action
beliefs_none = build_beliefs(actions, visibility={})
world = build_world(actions)

print("=== No Visibility ===")
print("Ground truth:", world)
print("Bob's beliefs:", beliefs_none["Bob"])
print("Carla's beliefs:", beliefs_none["Carla"])

# Bob observed Carla
beliefs_visible = build_beliefs(actions, visibility={"Bob": "Carla"})
print("\n=== Bob observed Carla ===")
print("Bob's beliefs:", beliefs_visible["Bob"])
print("Carla's beliefs:", beliefs_visible["Carla"])


# =============================================================================
# 2. Ordering IDs: relative position tags
# =============================================================================

def assign_ordering_ids(items):
    """
    Assign an OI (ordering ID) to each item based on first occurrence order.
    Returns: {item: oi}  where oi is 'first' or 'second'
    """
    labels = ["first", "second", "third"]  # extend as needed
    return {item: labels[i] for i, item in enumerate(items)}

characters = ["Bob", "Carla"]
objects    = ["bottle", "cup"]
states     = ["beer", "coffee"]

char_oi  = assign_ordering_ids(characters)
obj_oi   = assign_ordering_ids(objects)
state_oi = assign_ordering_ids(states)

print("\n=== Ordering IDs ===")
print("Characters:", char_oi)
print("Objects:   ", obj_oi)
print("States:    ", state_oi)


# =============================================================================
# 3. Co-location: binding OIs into the state token's slot
# =============================================================================

def bind_triples(actions, char_oi, obj_oi, state_oi):
    """
    For each (character, object, state) triple, store the character OI
    and object OI co-located at the state token's slot.
    This is the 'co-location' concept: the state token carries both OIs.
    """
    state_slots = {}
    for character, obj, state in actions:
        state_slots[state] = {
            "char_oi": char_oi[character],
            "obj_oi":  obj_oi[obj],
            "value":   state,
        }
    return state_slots

state_slots = bind_triples(actions, char_oi, obj_oi, state_oi)
print("\n=== Co-located State Slots ===")
for state, slot in state_slots.items():
    print(f"  '{state}' slot: {slot}")


# =============================================================================
# 4. Lookup (the lookback idea): given a question, retrieve the answer
# =============================================================================

def answer_belief_question(asking_about_char, asking_about_obj,
                            state_slots, beliefs, char_oi, obj_oi):
    """
    Given a question "what does <char> believe <obj> contains?",
    use the OI-based binding to retrieve the answer.

    Step 1 (binding lookback): find state slot where char_oi and obj_oi match
    Step 2 (answer lookback): retrieve the value from that slot
    """
    target_char_oi = char_oi.get(asking_about_char)
    target_obj_oi  = obj_oi.get(asking_about_obj)

    # Binding lookback: find the matching state slot
    matched_state = None
    for state, slot in state_slots.items():
        if slot["char_oi"] == target_char_oi and slot["obj_oi"] == target_obj_oi:
            matched_state = state
            break

    if matched_state is None:
        return "unknown"

    # Answer lookback: check the character's beliefs
    char_beliefs = beliefs.get(asking_about_char, {})
    return char_beliefs.get(asking_about_obj, "unknown")


print("\n=== Belief Questions ===")
for char in ["Bob", "Carla"]:
    for obj in ["bottle", "cup"]:
        answer = answer_belief_question(
            char, obj, state_slots, beliefs_none, char_oi, obj_oi
        )
        print(f"  What does {char} believe {obj} contains? → {answer}")
