# brick-stage

Tell stories with LEGO models that assemble themselves, in the style of an
instruction video. You write a story as a short script; brick-stage turns it
into a page that plays it back with a scrubbable timeline. Every model in the
story is checked by [brick-check](../brick-check), so the order the pieces fly
in is an order you could really build it in, and each model is exported as an
LDraw file you can open in BrickLink Studio.

## Make one

```sh
node build.mjs little-builder        # checks the models, writes out/little-builder/
open out/little-builder/index.html
node build.mjs test-chamber          # the puzzle-chamber story
```

Player keys: **space** plays or pauses, **← →** jump 2 s, **R** restarts,
**H** hides the controls (for recording), **F** goes fullscreen. Add `?t=12000`
to the URL to open on a given moment.

## Write a story

A story is a file in `stories/` that exports `story(meta, script)`:

```js
import { story, model, P } from "../lib/director.mjs";

// P(part, colour, x, y, z, rotation): studs across, plates up (a brick is 3).
// Parts are listed in build order.
const tower = model("tower", [P("3003", 15, 0, 0, 0), P("3003", 4, 0, 3, 0)]);

export default story({ title: "A Tower", drift: 1 }, (s) => {
  s.card("PROCEDURE 01", "Build a tower.");
  s.shot({ at: [1, 3, 1], az: 25, el: 15, dist: 14 }, 0);
  s.build(tower, { from: "above" });
  s.caption("Tower complete.");
  s.wait(2000);
});
```

| Action | What it does | Takes time? |
| --- | --- | --- |
| `card(kicker, title, { sub, dur })` | full-screen title card | yes |
| `build(model, { as, at, from, stagger, dur, onto })` | assembles a model piece by piece. `from`: `everywhere`, `above`, `below`, `left`, `right`, `front`. `onto` adds the parts to an existing actor, and the combined model is checked. | yes |
| `move(actor, [x, y, z], { dur, hop, steps })` | walks or glides an actor | yes |
| `turn(actor, degrees, { dur })` | turns an actor in place | yes |
| `unbuild(actor, { to, stagger })` | throws the pieces away, last first | yes |
| `wait(ms)` | holds | yes |
| `shot({ at, az, el, dist }, dur)` | eases the camera to a shot | no |
| `caption(text, kicker)` | shows a caption until the next one | no |
| `together(s => { … })` | starts actions at once; moves on after the longest | yes |

`meta.drift` slowly turns the camera, in degrees per second.

### Set pieces (see `stories/test-chamber.mjs`)

Set pieces are stage scenery, not LEGO. They aren't checked; the brick models
standing in them are.

| Action | What it does |
| --- | --- |
| `room({ w, d, h, dur })` | a white tiled room: the floor flips into place in a wave, then the back and right walls rise. Captions switch to big italic titles. |
| `figure(id, at)` | a pictogram figure. `move()` walks it (it faces where it's going), `turn()` turns it. |
| `button(id, at)` · `press(id)` · `release(id)` | a floor button |
| `door(id, { x, width, height })` · `open(id)` · `close(id)` | a sliding door in the back wall |
| `signal(id, points)` · `activate(id)` · `deactivate(id)` | a dotted line that draws itself, then lights up |

Brick models can be carried around a room with `move()`, as the test
object is in the chamber story.

## Rough edges

- Only plain bricks, plates and tiles from brick-check's catalog, rotated
  0° or 90°. No slopes, hinges or sideways building yet.
- Each model is checked on its own. Collisions *between* actors on the stage
  aren't checked.
- Characters can only be animated as a whole (walk, hop, turn). There's no
  posing of limbs.
