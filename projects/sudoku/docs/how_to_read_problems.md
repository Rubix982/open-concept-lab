# How to Read Problem Statements — Um\_nik (Upgraded & Actionable)

REF: `https://codeforces.com/blog/entry/62730`

---

## TL;DR — What to extract immediately

1. **Objects** (what entities exist?)
2. **Operations** (what can change them?)
3. **Goal** (what is being optimized/asked?)
4. **Constraints** (limits on n, values, special cases)
5. **Strange clause** (the unusual bit — usually the key)
6. **Small-sample behavior** (test 1-3 tiny cases by hand)

If you do those six things reliably, 80% of problems collapse into a known pattern.

---

## Cleaned Rules (short & repeatable)

* **Strip the story.** Convert narrative → nouns + actions + objective.
* **Shorter = clearer. Simpler = stronger.** If you can say the problem in one sentence, do it.
* **Limits are hints.** Small n → brute force; large n → log/n or linear solutions.
* **Samples are constraints.** Re-run them after modeling; they often expose misinterpretation.
* **Find the weirdness.** The "odd" sentence is usually the intended hook.
* **Rename objects.** Replace verbose descriptions with canonical names: "tree", "multiset", "interval", "graph" etc.
* **If you dislike a clause, change it.** Try the problem with a simpler version; then add complexity back.
* **Split the model.** If possible, decompose into independent subproblems.
* **Write the simplified statement on paper.** Handwriting helps crystallize thought.
* **Assume the setter is clever.** Nothing irrelevant is there by accident.

---

## Step-by-step Workflow (use this every time)

1. **Read full statement once** (don't panic about understanding everything).
2. **One-line summary** (write: "Given X, doing Y, find Z under constraints C").
3. **List tokens**: objects, operations, goal, constraints, examples, notes.
4. **Translate**: map story → canonical model (e.g., "connected graph with unique path" → `tree`).
5. **Scan for weird/small clauses** (e.g., "some edges weighted -1" or "at most one swap allowed"). Mark them.
6. **Check limits** and choose candidate classes: brute-force / greedy / DS / DP / graph / math.
7. **Mini-sanity check**: run through 1-3 tiny cases manually.
8. **Try simplifications**: remove or alter a clause to see if it becomes a known problem.

   * If it does, see if you can transform the original into that known problem (reduction).
9. **Sketch solution approach** (not full code): complexity, data-structures, invariants.
10. **If stuck:** attempt small constraints / make small examples / look for invariant or extremal element.
11. **Only then** begin coding or fully formalizing.

---

## Templates you can paste into scratch paper

### **One-line summary template**

> Given **\[objects]** with **\[properties]**, you may **\[operations]**. Find **\[goal]** under constraints **\[limits]**.

### **Simplified-statement template** (what you will hand someone)

> Math model: `G = (V, E)` (or array `A[ ]`, or multiset S). Operation: `op(...)`. Objective: `optimize/compute f(G/A/S)`. Limits: `n ≤ ...`.

### **Weird-clause checklist**

* Is there a parity / modulo mention? → check invariants.
* Is there a small bound (k ≤ 20)? → bitmask/meet-in-the-middle.
* Are edges/values negative? → beware Dijkstra.
* Is the graph "one simple path between any pair"? → Tree.
* Are operations reversible? → think backward.

---

## Russian-style Meta Tricks (with how to spot & apply them)

| Trick                        |                            How to spot it | Example micro-action                                                              |
| ---------------------------- | ----------------------------------------: | --------------------------------------------------------------------------------- |
| **Spot an invariant**        |     Repeatedly ask: "what never changes?" | Try 1-2 operations and see what total/parity remains constant.                    |
| **Reduce to canonical form** | Large messy story + known structure words | Replace narrative by `tree/graph/interval/array` and re-evaluate.                 |
| **Work backwards**           |      Objective seems simpler than process | Try to construct final states and reason reversely.                               |
| **Extremal principle**       |   Problem talks about "maximize/minimize" | Consider the largest/smallest element and its forced moves.                       |
| **Greedy guess + prove**     |        Problem has local choices per step | Try natural greedy; test on small cases to find counterexamples.                  |
| **Project/reduce dimension** |          Problem has multidim constraints | Collapse via projection (e.g., sort by key, reduce to 1D).                        |
| **Group by symmetry**        |                Many identical items/roles | Partition into equivalence classes and treat one representative.                  |
| **Count, don't simulate**    |       Operations countable or commutative | Derive formula for counts rather than simulate step-by-step.                      |
| **Transform operations**     |         Operation messy but deterministic | Replace operation by its effect on a simpler invariant (e.g., positions, counts). |
| **Memory-less reduction**    |                          State seems huge | Find minimal state descriptors (e.g., last index, count mod 2).                   |

---

## Worked mini-example (how to apply this to the Yandex game on tree)

We won't solve fully — we'll *model*.

**Raw short statement:** tree, vertices initially white. Players color vertices alternating red/blue. Score = #connected-components(red) − #connected-components(blue). Compute final score under optimal play.

**Modeling with the workflow:**

1. Objects: tree `T(V,E)`.
2. Operation: pick a white vertex and color red/blue alternately until none left.
3. Goal: final score `CR - CB`.
4. Limits: n ≤ 2e5 → need O(n log n) or O(n) solution.
5. Strange clause: scoring is components difference — not simply count of colored vertices. That's the hook.

**Simplify attempt:** express `components(red)` in terms of red vertices and red edges: for any color-class, components = (#vertices of that color) − (#edges fully inside that color). So score = (R − E\_R) − (B − E\_B) = (R − B) − (E\_R − E\_B). That reframes the problem to tracking edges inside colors. That's progress: maybe controlling which edges become "monochrome" matters more than raw vertex counts.

**Meta trick applied:** reduce operations → examine effect of coloring one vertex on local edges. Ask for extremal vertices, leaf handling, consider dynamic programming on tree or greedy anchored on leaves. Build small cases (n=1,2,3,4) and see behavior. This is how you find invariant / optimal local moves.

This is the sort of model transformation Um\_nik is hinting at — find algebraic expressions and local effects, then sum or DP.

---

## Practice Drills (make this daily)

1. **Read & condense (10 min):** take one Codeforces problem. Write one-line summary + simplified model. No code.
2. **Weird search (10 min):** list 3 "weird" clauses and hypothesize which known technique they point to.
3. **Micro-simulate (10 min):** make 3 tiny examples and play them by hand; record results.
4. **Simplify & map (20 min):** reduce the problem to canonical structures (tree, bipartite graph, interval, array) and write down the candidate algorithm family (DP/flow/greedy).
5. **Reflection (5 min):** what was the single insight? Write it as: "If you notice X, you map to Y."

Do this 4-5 times a week. After 3-4 weeks the "spot the strange" reflex becomes automatic.

---

## One-page Cheat Sheet (stick to screen/paper)

* Read once. Write one-line summary.
* Circle constraints and "strange" words.
* Map: story → canonical object (tree / array / graph / multiset / intervals).
* Ask: small n → brute? negative weights → Bellman-Ford? unique simple path → tree? parity mention → invariant?
* Tiny example: run it.
* If stuck: remove a clause or change it and see known problem.
* Final: sketch algorithm + complexity before coding.

---

## How this improves Um\_nik (direct improvements)

* **From anecdote → reproducible process:** convert his flavor into a repeatable checklist and templates.
* **From intuition → drills:** give short exercises that train the same instincts.
* **From raw examples → worked annotations:** walk through each of his sample problems step-by-step with the template.
* **From heuristics → decision rules:** produce "if X then likely Y" mappings (e.g., "small k ≤ 20 → bitmask DP").
