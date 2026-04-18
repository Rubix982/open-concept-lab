"""
Visibility lookback demo — why binding + answer lookback alone are insufficient
for the full ToM problem, and what the visibility lookback adds.
"""

import math
from dataclasses import dataclass, field
from typing import Literal, Optional

OrdinalID     = Literal[1, 2]
VisibilityRel = Literal["can_observe", "cannot_observe", "unspecified"]


# =============================================================================
# Types
# =============================================================================

@dataclass
class StoryEvent:
    character: str
    obj:       str
    state:     str
    char_oi:   OrdinalID
    obj_oi:    OrdinalID


@dataclass
class VisibilityCondition:
    observer:     str
    observed:     str
    observer_oi:  OrdinalID
    observed_oi:  OrdinalID
    relation:     VisibilityRel


@dataclass
class BeliefState:
    """What a character currently believes about each object."""
    character:  str
    beliefs:    dict[str, Optional[str]] = field(default_factory=dict)

    def knows(self, obj: str) -> Optional[str]:
        return self.beliefs.get(obj)

    def update(self, obj: str, state: str) -> None:
        self.beliefs[obj] = state


@dataclass
class VisibilityID:
    """
    A derived ID encoding the RELATION between observer and observed OIs.
    NOT the observer's OID. NOT the observed's OID.
    A new representation that is a function of both.
    """
    observer_oi:  OrdinalID
    observed_oi:  OrdinalID

    @property
    def value(self) -> float:
        """Encode relation as a single value (in real model: a vector in a subspace)."""
        return float(self.observer_oi) * 10.0 + float(self.observed_oi)


# =============================================================================
# Step 1 — Binding + Answer Lookback (what we already had)
# =============================================================================

def binding_lookback(
    query_char_oi: OrdinalID,
    query_obj_oi:  OrdinalID,
    events:        list[StoryEvent],
) -> Optional[StoryEvent]:
    """Find the event where this character acted on this object."""
    for e in events:
        if e.char_oi == query_char_oi and e.obj_oi == query_obj_oi:
            return e
    return None


def answer_lookback(event: Optional[StoryEvent]) -> Optional[str]:
    """Retrieve the state value from the matched event."""
    return event.state if event else None


# =============================================================================
# Step 2 — Visibility Lookback (the new mechanism)
# =============================================================================

def generate_visibility_id(condition: VisibilityCondition) -> VisibilityID:
    """
    Generate a Visibility ID from the observer-observed relation.
    This is a DERIVED representation — not either character's OID alone.
    In the real model: a vector produced by an attention head reading both OIDs.
    """
    return VisibilityID(
        observer_oi=condition.observer_oi,
        observed_oi=condition.observed_oi,
    )


def visibility_lookback(
    vis_id:        VisibilityID,
    query_obj_oi:  OrdinalID,
    events:        list[StoryEvent],
) -> Optional[str]:
    """
    Use the Visibility ID to find what the OBSERVED character did to this object,
    then return that state — to be written into the OBSERVER's belief.

    The visibility_id tells us: "look for the observed character's actions"
    vis_id.observed_oi is the char_OI of the character being observed.
    """
    event = binding_lookback(
        query_char_oi=vis_id.observed_oi,
        query_obj_oi=query_obj_oi,
        events=events,
    )
    return answer_lookback(event)


# =============================================================================
# Full belief resolution — combining all three lookbacks
# =============================================================================

def resolve_belief(
    asking_about_char: str,
    asking_about_obj:  str,
    events:            list[StoryEvent],
    visibility_graph:  list[VisibilityCondition],   # directed edges — each must be stated explicitly
    char_oi_map:       dict[str, OrdinalID],
    obj_oi_map:        dict[str, OrdinalID],
) -> tuple[str, str]:
    """
    Resolve what a character believes about an object's state.
    Returns (answer, explanation of which mechanism fired).

    visibility_graph is a list of DIRECTED edges. Bob seeing Carla and
    Carla seeing Bob are two separate entries. Neither implies the other.
    """
    char_oi = char_oi_map[asking_about_char]
    obj_oi  = obj_oi_map[asking_about_obj]

    # --- Binding + Answer Lookback ---
    # Did this character directly interact with this object?
    event  = binding_lookback(char_oi, obj_oi, events)
    answer = answer_lookback(event)

    if answer:
        return answer, "binding + answer lookback (character acted directly)"

    # --- Visibility Lookback ---
    # Does this character have a directed visibility edge to someone
    # who interacted with this object?
    for condition in visibility_graph:
        if condition.observer != asking_about_char:
            continue                          # this edge is not about the asking character
        if condition.relation != "can_observe":
            continue                          # explicitly cannot observe — skip

        vis_id = generate_visibility_id(condition)
        answer = visibility_lookback(vis_id, obj_oi, events)
        if answer:
            return answer, (
                f"visibility lookback "
                f"({asking_about_char} → {condition.observed}, "
                f"vis_ID={vis_id.value})"
            )

    return "unknown", "no lookback matched — character has no knowledge of this object"


# =============================================================================
# Run scenarios
# =============================================================================

events: list[StoryEvent] = [
    StoryEvent("Bob",   "bottle", "beer",   char_oi=1, obj_oi=1),
    StoryEvent("Carla", "cup",    "coffee", char_oi=2, obj_oi=2),
]

char_oi_map: dict[str, OrdinalID] = {"Bob": 1, "Carla": 2}
obj_oi_map:  dict[str, OrdinalID] = {"bottle": 1, "cup": 2}

questions: list[tuple[str, str]] = [
    ("Bob",   "bottle"),
    ("Bob",   "cup"),
    ("Carla", "bottle"),
    ("Carla", "cup"),
]

def run_scenario(
    label:            str,
    visibility_graph: list[VisibilityCondition],
) -> None:
    print("=" * 60)
    print(f"SCENARIO: {label}")
    print("Visibility edges:")
    if not visibility_graph:
        print("  (none)")
    for c in visibility_graph:
        arrow = "→ can observe" if c.relation == "can_observe" else "→ cannot observe"
        print(f"  {c.observer} {arrow} {c.observed}")
    print()
    for char, obj in questions:
        answer, mechanism = resolve_belief(
            char, obj, events,
            visibility_graph=visibility_graph,
            char_oi_map=char_oi_map,
            obj_oi_map=obj_oi_map,
        )
        print(f"  {char} + {obj:8s} → {answer:10s}  ({mechanism})")
    print()


# --- Scenario A: No visibility ---
run_scenario("No visibility", visibility_graph=[])

# --- Scenario B: Bob → Carla only (one-way) ---
run_scenario(
    "Bob can observe Carla  (Carla does NOT observe Bob)",
    visibility_graph=[
        VisibilityCondition("Bob", "Carla", observer_oi=1, observed_oi=2, relation="can_observe"),
        # No reverse edge — Carla's knowledge of Bob's actions is unaffected
    ],
)

# --- Scenario C: Carla → Bob only (reverse one-way) ---
run_scenario(
    "Carla can observe Bob  (Bob does NOT observe Carla)",
    visibility_graph=[
        VisibilityCondition("Carla", "Bob", observer_oi=2, observed_oi=1, relation="can_observe"),
    ],
)

# --- Scenario D: Mutual visibility ---
run_scenario(
    "Bob ↔ Carla  (both observe each other — two explicit directed edges)",
    visibility_graph=[
        VisibilityCondition("Bob",   "Carla", observer_oi=1, observed_oi=2, relation="can_observe"),
        VisibilityCondition("Carla", "Bob",   observer_oi=2, observed_oi=1, relation="can_observe"),
    ],
)

# --- Scenario E: Explicit cannot observe (neither direction) ---
run_scenario(
    "Bob cannot observe Carla  +  Carla cannot observe Bob",
    visibility_graph=[
        VisibilityCondition("Bob",   "Carla", observer_oi=1, observed_oi=2, relation="cannot_observe"),
        VisibilityCondition("Carla", "Bob",   observer_oi=2, observed_oi=1, relation="cannot_observe"),
    ],
)

print("=" * 60)
print("KEY POINT — Directed vs Symmetric")
print("=" * 60)
print("""
  The visibility relation is a DIRECTED edge in a graph, not a property
  of a pair. Bob → Carla and Carla → Bob are independent edges.
  Each one generates its own Visibility ID:

    Bob   → Carla:  vis_ID = f(observer_OI=1, observed_OI=2)  = 12.0
    Carla → Bob:    vis_ID = f(observer_OI=2, observed_OI=1)  = 21.0

  Different IDs. Different pointers. Different lookbacks.

  If only Bob → Carla is stated, Carla's beliefs about Bob's actions
  are unaffected — the reverse edge simply does not exist in the graph.
  The model does not infer it. It must be explicitly specified.
""")
