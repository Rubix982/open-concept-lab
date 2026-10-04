# The presenter: a LEGO minifig host

A minifigure (the rigged kit in `lib/minifig.js`) on a 4×4 plate, in its own
3D stage, lit like the brick charts. It walks on, gestures, points at anchors
on other stages, and talks while captions play.

```js
s.bricks("bars", bars, { x: 520, y: 60, w: 1400, h: 1000 });          // the chart first…
s.presenter("host", { x: 40, y: 330, w: 560, h: 720,                  // …then the host
  look: { torso: 1, legs: 72, print: "sweater", hat: "cap", hatColor: 4 } });
s.walkIn("host");
s.together((g) => { g.present("host", "wave", { dur: 2600 }); g.narrate("Hi!"); });
s.present("host", "point", { at: { obj: "bars", at: "bar0" }, dur: 3000 });
s.face("host", "grin");
s.walkOut("host");
```

## Verbs (`lib/actions/presenter.mjs`)

| Verb | What it does |
| ---- | ------------ |
| `s.presenter(id, o)` | Creates the host. `x, y, w, h` is its rect in the 1920×1080 frame; `look` is a minifig look (`torso`, `legs`, `print`, `hat`, `hatColor`, `face`, `beard`, `extra`); `side` is where it enters and leaves (`"left"`/`"right"`); `plate` is the plate colour; `standing: true` starts it on the plate, otherwise it waits offstage for `walkIn`; `talkOnNarration` (default true). |
| `s.walkIn(id, { dur, side })` | Walks on from the side, legs and arms swinging, then turns to the camera. |
| `s.walkOut(id, { dur, side })` | Turns and walks off the way it came. |
| `s.present(id, gesture, { dur, strength, face, at })` | A gesture for `dur` ms, eased in and out: `wave`, `point`, `talk`, `shrug`, `nod`, `think`. `point` needs `at`: `{ obj, at }` (a named anchor on a brick stage), `{ obj, col, row }` (a node on a layer stack) or `{ x, y }` (a frame point). |
| `s.face(id, expr)` | `smile`, `grin`, `neutral`, `sad`, `worried`, `surprised`, `determined`, `deadpan`. |

Gestures are 0..1 strengths tweened on the stage's props and can overlap
(point while talking, nod while waving). The player turns them into joint
angles as a pure function of time, so a render lands on the same pose as the
live page.

## Behaviour worth knowing

- **Pointing** uses the arm on the target's side, swung out at the target's
  angle from the shoulder, with the body (±28°) and head turned toward it.
- **Order doesn't matter for pointing.** The presenter's stage is flagged
  `after`, so the player updates it once every other 3D camera has moved for
  the frame; it always aims at where the target is now.
- **Talking** is automatic while a caption is on screen (`talkOnNarration`):
  a head bob, a little sway and a gesturing free hand, eased at each line's
  start and end. A `talk` gesture forces it.
- **The rect clips.** The host walks from just outside its own rect; make the
  rect reach the frame edge if it should enter from off screen.

## Files

- `lib/plugins/presenter.js`: the `presenter` stage kind (`BP.stage`), the
  gesture-to-joint mapping and pointing.
- `lib/plugins/presenter.build.mjs`: inlines `lib/minifig.js` when a script
  has a presenter, and sets the colour table.
- `lib/actions/presenter.mjs`: the verbs.
- `scripts/cap-presenter.mjs`: the capability test (24 s: walk in, wave,
  point at the slowest and fastest bar of the cache-router chart, shrug, nod,
  think, walk out).
