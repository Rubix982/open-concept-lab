# brick-stage TODO

Where this is heading: a manim-style tool for explaining ideas in videos, with
a LEGO look. Two pipelines, in this order:

1. **Ingestion:** any shape becomes a checked brick model plus a story.
2. **Explain:** scripts with narration, text, maths and morphs, rendered to video.

Each item is proven on something real before the next one starts.
`[~]` marks work in progress.

## Pipeline 1: ingestion

- [x] Universal loader: GLB/glTF, OBJ with materials and textures, STL, PLY,
      MagicaVoxel `.vox` (`brick-check/tools/mesh-load.mjs`)
- [x] Showcase end to end on real downloads: the Avocado glTF sample (CC0) and
      Keenan Crane's Spot cow (CC0)
- [x] Colour clustering for baked-in lighting (a yellow duck stays yellow)
- [x] Image → 3D via Hugging Face (`brick-check/tools/image-to-3d.mjs`): a hand
      drawing became a duck model via InstantMesh (Apache-2.0). TripoSG (MIT)
      is tried first, but its GPU worker was failing on 2026-10-04.
- [ ] Text → image → 3D: a text-to-image step in front of image-to-3D
- [ ] Brickify with bricks, not only plates: merge 3-plate stacks into bricks
      (about half the parts, faster scenes)
- [ ] Recover brickify's dropped plates using sideways (slide) insertion
- [ ] Sections that understand parts (arms, head), not only height bands
- [x] Bigger palette (21 colours, LDraw = Rebrickable codes), colour matching,
      automatic sections, `showcase.mjs`

## Framework hardening

- [ ] Performance for big models: instance identical parts (670-part scenes
      stutter)
- [x] Stage check aware of joints (swung parts checked stud by stud), and
      `contact()` for touching on purpose
- [ ] Stage check against set pieces (room, button, door)
- [ ] brick-check: tidy package.json and the npm dependencies, one test command

## Milestone: The Bridge to Gus (`stories/bridge-to-gus.txt`)

A 4–5 minute brickfilm with characters and a colour script, used to test the
storytelling side of the framework. Built in vertical slices, each ending in
footage:

- [x] **Minifigures:** rigged figures (head, arms, C-shaped hands, legs),
      walking, faces as expressions, outfits and hats. Characters, not checked
      LEGO.
- [x] **Props in hand:** `hold()` and `drop()`; a prop rides on a hand and moves
      with the arm
- [x] **Arcs and tumbles:** throws with height and spin; bending structures on
      joints (the bridge sags, then folds)
- [x] **Transparent parts:** trans-blue, trans-yellow, trans-orange, trans-clear
- [x] **Lights as actors:** a sunlight patch that moves, clouds dimming it, a lamp
      cone, a lighthouse beam that sweeps, lamps switching on and off
- [x] **A richer colour script:** overcast, amber, violet dusk, plus custom moods
- [x] **Sound in the render:** sound effects (creak, tik, yip, knock, click),
      room ambience, music that rises
- [ ] **Depth of field:** blurry giant props (a sock, a pencil) to sell the scale
- [ ] **Scenery props:** non-LEGO shapes for the bedroom
- [ ] Slice 1: Scenes 1–2 (bakery, the round-hands gag, river, lighthouse)
- [ ] Slice 2: Scene 4 (the collapse, the light draining, the lamp going dark)
- [ ] Slice 3: Scenes 5–6 (the minifig chain, the lighthouse beam)
- [ ] The whole film, rendered with sound

## Capability suite (`stories/capabilities/`, `node build.mjs --capabilities`)

- [x] walk and gesture · faces and outfits · hold, carry, drop · arcs and
      tumbles (and `hatFly`) · joints and folding · sunlight and clouds · moods ·
      sound cues (balanced to within 5 dB)
- [ ] camera moves · speech and captions · particles · instruction mode
- [ ] Run the suite automatically: render a frame sheet per test and compare it
      with the last good one

## Pipeline 2: explain (manim-style)

- [x] `render.mjs`: a story to MP4, frame-perfect, no screen recording
      (Rated for Two: 1080p60, 1,839 frames)
- [x] Narration lines → subtitles (`s.narrate("…")`; scenes wait for the
      line; the render writes an .srt, `--subs` burns them in)
- [ ] Audio in the render: the story's sound effects and music as a track
- [ ] Pace scenes from a recorded voice track
- [ ] Explainer vocabulary: `text()` that writes itself on, `math()` (LaTeX),
      `arrow(a, b)`, `label()`, `counter()`, boxes
- [ ] `morph(a → b)`: bricks fly from one model into another
- [ ] Brick charts and diagrams: bar charts, number lines, grids
- [ ] A real first video: the Difference Engine or DataScalar
- [ ] A story-writing guide for AI (and people): the actions, pacing, common
      mistakes
