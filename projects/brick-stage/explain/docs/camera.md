# Camera, transitions and formats

Everything here is in the core (`lib/script.mjs`, `lib/blueprint.js`) and
works for both 3D stage kinds, `s.bricks(...)` (LEGO) and `s.stage3d(...)`
(the glowing layer stack). See `scripts/cap-camera.mjs` and
`scripts/cap-vertical.mjs`.

## Camera

A 3D stage's camera sits on a sphere around a target. The target can be
moved or pulled to an anchor, and every value is an ordinary tweenable prop.

| Prop | Meaning |
| ---- | ------- |
| `az`, `el`, `dist` | angle around, angle above, distance from the target |
| `tx`, `ty`, `tz` | the target in world units (default: the model's centre, half its height up) |
| `focus` | an anchor the target is pulled to — bricks: an anchor name (`"cell:3:10"`, `"bar2"`); stack: `"col:row"` |
| `focusK` | how far the pull has gone, 0 → 1 (set by `lookAt`) |
| `drift` | a subtle handheld wobble on az/el/dist, e.g. `0.3`; deterministic, so renders repeat exactly |

```js
s.lookAt("heat", "cell:3:10", { dur: 1400 });   // pull the target to an anchor
s.lookAt("heat", null);                         // back to the model's centre
s.shot("heat", "hero");                         // low three-quarter
s.shot("heat", "top");                          // plan view
s.shot("heat", "side");                         // edge-on from the side
s.shot("heat", "closeup:cell:3:10");            // dolly in on an anchor (o.zoom, default 0.42 of the opening distance)
s.shot("heat", "wide");                         // back to the opening framing
s.shot("cols", "orbit", { deg: 80, dur: 6000 }); // a slow continuous turn (linear)
s.bricks("cols", chart, { drift: 0.6 });        // handheld drift for the whole shot
```

Every preset is a `set()` of camera props (eased, `o.dur` default 1.8 s), and
takes overrides: `{ az, el, zoom, dur, ease }`. Presets other than `closeup`
release a focus unless `{ keepFocus: true }`.

The verb is `lookAt`, not `focus`: `s.focus` belongs to code panels (the
marks plugin), where it moves the highlight bar.

Plugins drawing their own 3D stages can use the same camera with
`BP.aim(camera, props, t, baseTarget, focusAt)`.

## Explore (live page only)

While the page is paused, drag a 3D stage to orbit it and scroll to zoom.
Press play and the scripted camera takes over again. Renders
(`__renderAt`) and posters never see the viewer's camera.

## Transitions

```js
s.transition("grid");        // also "wipe", "iris", "glitch", "blueprint-fold"; { dur }
s.clear(["heat"], { dur: 1 }); // changes under the cover
s.heading("next chapter");
```

A sheet of blueprint paper covers the frame by the transition's midpoint and
uncovers it by the end. The clock stops at the midpoint, so whatever the
script does next happens under the cover and is revealed. Each kind has its
own sound (`t-<kind>` voice). Transitions are drawn after every object
(`BP.TRANSITIONS` holds them by name; a plugin can add a kind there).

## Formats

```js
explainer({ title: "…", format: "vertical" }, (s) => { … });   // 1080×1920
explainer({ title: "…", format: "square" }, …);                 // 1080×1080
explainer({ title: "…", w: 1280, h: 720 }, …);                  // any size
```

The background, crop marks, ruler ticks, dial (top right), default centred
text/tokens/chips and full-frame 3D stages follow the frame. The page keeps
the timeline's aspect ratio and sizes captions to the frame. Render at a
matching size: `node render.mjs <name> --size 1080x1920`.

A tall frame shows less of a wide model: pull the camera back and turn it
along the model (`cap-vertical` uses `az: -52, dist: 64` for a 27-stud chart).

## Posters

```bash
node explain/poster.mjs <name>            # → out/<name>/poster.jpg at the explainer's own size
node explain/poster.mjs <name> 9000       # at 9 s
node explain/poster.mjs <name> --out x.jpg
```

Without a time it picks the longest 3D build, finished and still on screen,
in the longest stretch where its camera isn't moving (no 3D stage: 40% in).
