# Engineer Tickets

### E-001 · Orbitable 3D cube viewer

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-13
**Updated:** 2026-09-13

**Description:**
Render a solved 3x3x3 cube in OpenGL via pygame. 26 visible cubies, black
plastic bodies, inset stickers in the standard Western colour scheme. Left-drag
orbits the view in screen axes (not cube axes), scroll zooms, R resets, Esc
quits.

**Artifacts:**

- cube.py
- requirements.txt

**Closed:** 2026-09-13

---

### E-002 · Face turns, scramble, and solve-by-undo

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-13
**Updated:** 2026-09-13

**Description:**
Give the cube real state and motion.

1. State: each cubie carries a grid position and a 3x3 orientation matrix; its
   sticker colours are fixed in its own local frame at construction. A quarter
   turn selects the 9 cubies on one layer, left-multiplies their position and
   orientation by the 90-degree rotation, and re-rounds the position to the
   integer grid.
2. Animation: turns are queued and played one at a time over a fixed duration;
   the layer's cubies get an extra world-space rotation of `t * 90` degrees
   while the turn is in flight. State commits on completion, never mid-flight.
3. Mouse turns: on left-press, cast a ray from the cursor into cube space and
   intersect the cubie AABBs to find the grabbed face. On drag past a pixel
   threshold, pick whichever of the face's two in-plane axes best matches the
   drag direction on screen, and rotate about `axis = drag_dir x face_normal`
   at the grabbed cubie's layer. A press that misses the cube orbits instead.
4. Keyboard turns: U/D/L/R/F/B, Shift for counter-clockwise.
5. Scramble (S): enqueue ~25 random quarter turns, recorded to history.
6. Solve (Enter): enqueue the inverse of the recorded history in reverse order.
   This un-does the scramble; it is not a general solver (deferred to v2).

**Blockers:** none

**Artifacts:**

- cube.py
- agents/shared/decisions.md → "Solve-by-undo instead of a real solver"
- README.md, docs/cube.png

**Verified:** 4x U is the identity; 200 random turns leave 26 distinct grid
slots and undo cleanly; scramble/solve round-trips through the real queue;
raycast never picks a face pointing away from the camera; a rendered U turn
moves the right face's colours onto the front-top row.

**Closed:** 2026-09-13
