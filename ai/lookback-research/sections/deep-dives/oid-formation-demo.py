"""
How Ordering IDs (OIDs) are formed and why char_OI and obj_OI match.

No ML libraries. Expresses the structural logic of OID assignment and lookup.
"""

from dataclasses import dataclass
from typing import Literal, Optional

OrdinalID = Literal[1, 2]  # "first" or "second" — the only two values


# =============================================================================
# Step 1: the story has a parallel structure
# =============================================================================

@dataclass
class StoryEvent:
    """One action in the story: a character acts on an object producing a state."""
    character: str
    obj: str
    state: str
    ordinal: OrdinalID  # which event is this — first or second?


def parse_story(events: list[tuple[str, str, str]]) -> list[StoryEvent]:
    """
    Assign ordinal IDs by reading order — first mention = 1, second = 2.
    The model doesn't know names; it knows order.
    """
    return [
        StoryEvent(character=char, obj=obj, state=state, ordinal=i + 1)
        for i, (char, obj, state) in enumerate(events)
    ]


story_events = parse_story([
    ("Bob",   "bottle", "beer"),    # first event  → ordinal 1
    ("Carla", "cup",    "coffee"),  # second event → ordinal 2
])

print("=== Story events with assigned ordinals ===")
for e in story_events:
    print(f"  ordinal={e.ordinal}: {e.character} → {e.obj} → {e.state}")


# =============================================================================
# Step 2: OID tables — each entity gets an OID from its event's ordinal
# =============================================================================

@dataclass
class OIDTables:
    char_oid:  dict[str, OrdinalID]
    obj_oid:   dict[str, OrdinalID]
    state_oid: dict[str, OrdinalID]


def build_oid_tables(events: list[StoryEvent]) -> OIDTables:
    """
    Extract three separate OID tables — one per entity type.
    Each entity's OID = the ordinal of the event it appeared in.
    """
    return OIDTables(
        char_oid=  {e.character: e.ordinal for e in events},
        obj_oid=   {e.obj:       e.ordinal for e in events},
        state_oid= {e.state:     e.ordinal for e in events},
    )


oids = build_oid_tables(story_events)

print("\n=== OID tables ===")
print("  char_OID: ", oids.char_oid)
print("  obj_OID:  ", oids.obj_oid)
print("  state_OID:", oids.state_oid)

print("\n  Key observation:")
print("  Bob=1, bottle=1, beer=1  → all '1' because they're from the same event")
print("  Carla=2, cup=2, coffee=2 → all '2' because they're from the same event")
print("  The alignment isn't accidental — it's structural.")


# =============================================================================
# Step 3: binding — write char_OID and obj_OID into the state token's slot
# =============================================================================

@dataclass
class StateTokenSlot:
    """
    The state token's residual stream carries:
    - its own value
    - the char_OID of who produced it      ← written via attention from char token
    - the obj_OID of what was acted on      ← written via attention from obj token

    Both OIDs end up here because the model read:
    "<char> grabs <obj> and fills it with <state>"
    and learned to route both OIDs into the state's slot.
    """
    value:    str
    char_oid: OrdinalID
    obj_oid:  OrdinalID


def build_state_slots(events: list[StoryEvent], oids: OIDTables) -> dict[str, StateTokenSlot]:
    return {
        e.state: StateTokenSlot(
            value=    e.state,
            char_oid= oids.char_oid[e.character],
            obj_oid=  oids.obj_oid[e.obj],
        )
        for e in events
    }


state_slots = build_state_slots(story_events, oids)

print("\n=== State token slots (co-located OIDs) ===")
for name, slot in state_slots.items():
    print(f"  '{name}': char_OID={slot.char_oid}, obj_OID={slot.obj_oid}, value={slot.value}")

print("\n  'beer' carries char_OID=1 (Bob) AND obj_OID=1 (bottle) — same slot, same token.")
print("  This is WHY they match: the model wrote both from the same sentence.")


# =============================================================================
# Step 4: lookup — the two-step lookback
# =============================================================================

@dataclass
class BeliefQuery:
    asking_about_char: str
    asking_about_obj:  str


def binding_lookback(
    query: BeliefQuery,
    oids: OIDTables,
    state_slots: dict[str, StateTokenSlot],
) -> Optional[StateTokenSlot]:
    """
    Step 1: given a char and obj name, find the state slot where both OIDs match.
    This is the binding lookback — it resolves (char, obj) → state slot.
    """
    target_char_oid = oids.char_oid.get(query.asking_about_char)
    target_obj_oid  = oids.obj_oid.get(query.asking_about_obj)

    if target_char_oid is None or target_obj_oid is None:
        return None

    for slot in state_slots.values():
        if slot.char_oid == target_char_oid and slot.obj_oid == target_obj_oid:
            return slot

    return None


def answer_lookback(slot: Optional[StateTokenSlot]) -> str:
    """
    Step 2: given the matched state slot, return the value.
    This is the answer lookback — it dereferences the slot to the actual state.
    """
    return slot.value if slot else "unknown"


print("\n=== Belief queries ===")
queries: list[BeliefQuery] = [
    BeliefQuery("Bob",   "bottle"),
    BeliefQuery("Bob",   "cup"),      # Bob never saw Carla → unknown
    BeliefQuery("Carla", "cup"),
    BeliefQuery("Carla", "bottle"),   # Carla never saw Bob → unknown
]

for q in queries:
    slot  = binding_lookback(q, oids, state_slots)
    answer = answer_lookback(slot)
    match_info = f"char_OID={slot.char_oid}, obj_OID={slot.obj_oid}" if slot else "no match"
    print(f"  '{q.asking_about_char} + {q.asking_about_obj}' → [{match_info}] → {answer}")
