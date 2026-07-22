# Experiment: Counterfactual Neighbor Generation

**Goal:** Automatically generate neighbor queries for any edit triple.

## The problem

Writing neighbor queries by hand (as in E-003) doesn't scale. We need a way
to generate N1, N2, and reverse queries programmatically given any
(subject, relation, object, new_object) tuple.

## Approach

Use Wikidata to expand the subject entity into its property graph:
- Subject S has properties P1=V1, P2=V2, ...
- After editing R: O → O*, find all properties of O* that differ from O
- Those differences are the candidate neighbor facts

Example:
  Edit: Eiffel Tower → location → Paris → Rome
  Wikidata(Paris):  country=France, language=French, currency=Euro
  Wikidata(Rome):   country=Italy,  language=Italian, currency=Euro
  Differences: country (France→Italy), language (French→Italian)
  → These become N1 and N2 neighbor queries automatically

## Implementation sketch

```python
import requests

def get_wikidata_properties(entity_label: str) -> dict:
    # SPARQL query to Wikidata for entity properties
    ...

def generate_neighbors(subject, relation, old_obj, new_obj) -> list[dict]:
    old_props = get_wikidata_properties(old_obj)
    new_props = get_wikidata_properties(new_obj)
    neighbors = []
    for prop in old_props:
        if old_props[prop] != new_props.get(prop):
            neighbors.append({
                "type": "N1_logical",
                "property": prop,
                "old_value": old_props[prop],
                "new_value": new_props[prop]
            })
    return neighbors
```

This unlocks automatic evaluation at scale — no manual query writing.
