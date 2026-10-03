# brick-stage

Tell stories with LEGO models that assemble themselves, in the style of an
instruction video. You write a story as a short script; brick-stage turns it
into a page that plays it back with a scrubbable timeline. Every model in the
story is checked by [brick-check](../brick-check), so the order the pieces fly
in is an order you could really build it in, and each model is exported as an
LDraw file you can open in BrickLink Studio.

New here? **[GUIDE.md](GUIDE.md)** gets a first story on screen in five minutes.

## Make one

```sh
node new.mjs my-story "My Story"     # start a story from the template
node dev.mjs little-builder          # live preview at http://localhost:5173
node build.mjs little-builder        # checks the models and the stage, writes out/little-builder/
node build.mjs --all                 # every story, plus a gallery at out/index.html
node booklet.mjs little-builder      # printable instructions for a model, as HTML and PDF
node --test test/*.test.mjs
node build.mjs --capabilities        # the capability suite: one small scene per ability
```

`stories/capabilities/` holds one short scene per ability (walking and gesture,
faces and outfits, holding and throwing, arcs and tumbles, joints folding,
sunlight and clouds, moods, sound cues). Build them after changing the player
or the director, and look at them: they're how regressions show up.

With `dev.mjs` running, every save rebuilds the story and the open page
reloads at the moment you were watching.

The build checks two things and says so in the terminal and on the page:

- **Every model** goes through brick-check. A model that can't be built shows
  its problem parts glowing red, with the reasons in the corner badge.
- **The stage:** the whole timeline is run looking for actors that walk into
  each other. Each overlap is listed with a link to the moment it happens.

Press **I** (or the Steps button) for **instruction mode**: playback stops at
the end of each build step and shows the parts that step needs, with the new
parts outlined in yellow and earlier ones pale, the way an instruction booklet
draws them. In this mode, **← →** move between steps.

Player keys: **space** plays or pauses, **← →** jump 2 s, **[ ]** jump between
chapters (one per caption), **M** sound, **R** restarts, **H** hides the
controls (for recording), **F** goes fullscreen. Add `?t=12000` to the URL to
open on a given moment.

Sound is synthesised in the browser from the timeline: bricks click as they
land, figures step, buttons thunk, doors slide. It starts muted; press M.

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
| `turnTo(actor, target, { dur })` | turns to face a heading, `"camera"`, or another actor, the short way round | yes |
| `unbuild(actor, { to, stagger })` | throws the pieces away, last first | yes |
| `pose(actor, joint, degrees, { dur })` | swings a joint to an angle (0 is the rest pose) | yes |
| `say(actor, text, { dur })` | a speech bubble over an actor | yes |
| `fadeOut({ dur, color })` · `fadeIn({ dur })` | fades the picture out and back | yes |
| `attach(sub, { onto, at })` | flies a finished sub-assembly onto another actor; from then on it moves with it, and the combined model is checked | yes |
| `wait(ms)` | holds | yes |
| `shot({ at, az, el, dist }, dur)` | eases the camera to a shot | no |
| `follow(actor, { az, el, dist, offset })` | keeps the camera on an actor as it moves | no |
| `orbit(degrees, { dur })` | swings the camera around the current target | no |
| `highlight(actor, { dur, color })` | a pulsing glow, to draw the eye | no |
| `callout(text, { on, at, offset, dur })` | a label on a leader line, pinned to an actor or a point | no |
| `emit(kind, { on, at, count, dur })` | particles: `hearts`, `sparkles` or `confetti` | no |
| `mood(name, { dur })` | the light: `day`, `sunset` or `night` (stars and a moon) | no |
| `letterbox(on, { dur })` | cinema bars | no |
| `music(name)` | a generated chord pad, `romance` or `wonder`; `null` stops it | no |
| `section(title)` | starts a numbered section of the build (a chapter and a caption) | no |
| `contact(a, b)` | two actors touch on purpose (a collapse, a splash), so the stage check doesn't report it | no |
| `minifig(id, at, { look })` · `face(id, expr)` | a rigged character; expressions | `minifig` yes |
| `hold(fig, hand, prop)` · `drop(prop, { to })` | a prop rides on a hand; let go to land somewhere | `drop` yes |
| `hatFly(fig, { to })` | a hat flies off, to a point or onto another figure's head | yes |
| `light(id, { kind })` · `lightTo(id, { … })` · `lamp(actor, on)` | spots with beams, glows, window light; a model's lamp | no |
| `sfx(name)` · `ambience("room")` | sound effects on cue; a room bed | no |
| `turnaround(actor, { dur })` | circles the camera once around an actor | no |

`build(…, { from: "path" })` flies each part in along the way brick-check
says it really goes in: straight down, up from below, or slid in from the side.

### Joints

A model can name groups of parts that swing on a pivot:

```js
model("robot", parts, { joints: {
  "right-arm": { parts: [8, 9, 11], pivot: [4.5, 10, 0.5], axis: "x" },
} });
```

`axis` is `x` (forward and back), `z` (sideways) or `y` (twist). The model is
checked in its rest pose. A joint is artistic licence unless the real build
puts a hinge there. The robot in `stories/cast/robot.mjs` has both arms and
its head on joints.

### From the Microduck booklet

Several features come from reading the
[Microduck booklet](https://huggingface.co/buckets/victor/microduck-lego-booklet)
(unofficial fan-made instructions for a LEGO model of Pollen Robotics'
Microduck), and doing what it does:

- **Real parts in real colours.** Every model is checked against Rebrickable's
  catalogue. The build warns about any part LEGO never made in that colour, and
  each model's parts list (`models/<model>.csv`) carries LEGO element IDs.
- **Insertion paths,** including "slide in" steps, recorded by the checker and
  usable for animation (`from: "path"`).
- **Sections and sub-assemblies** (`section()`, `attach()`).
- **Booklet-style steps** in the player (I), and **printable booklets**
  (`booklet.mjs`): cover, parts inventory with element IDs, every step at one
  scale, a front/left/back/right turnaround, and what was and wasn't checked.
- **Real-world size and estimated weight** for each model.
- **Being honest about testing.** The player and every booklet say plainly that
  nothing has been built with real bricks.
- **Mirror images** for left/right pairs: `mirror(parts, { axis })`, exported
  from the director.
- **Shapes from CAD.** brick-check's `tools/brickify.mjs` samples a 3D mesh
  into a buildable grid of plates, the booklet's "shape sampled from the
  robot's own CAD model". `fitToCatalogue()` then recolours any plate LEGO
  doesn't make in its colour. `stories/microduck.mjs` builds the result, made
  from Pollen Robotics' open Microduck CAD (`node ../brick-check/tools/microduck-model.mjs`
  regenerates it): 670 plates, built in sections, with the head made as a
  sub-assembly and set on the neck.

### From any 3D shape: the input pipeline

No CAD needed. Any of these becomes a checked brick model plus a story:

```sh
node showcase.mjs avocado.glb "An Avocado" --height 40 --credit "Avocado by Microsoft, CC0"
```

`showcase.mjs`:
1. loads the file (GLB/glTF, OBJ with materials and textures, STL, PLY, or a
   MagicaVoxel `.vox`)
2. matches its colours, including texture colours, to the nearest LEGO
   colours, keeping the most-used few
3. samples the shape into plates (brickify), keeping only parts LEGO makes in
   each colour, and checks the result
4. finds sections at the model's narrow points, with a top part that stands
   alone becoming a sub-assembly
5. writes an editable story (`stories/<name>.mjs`), the animation, a booklet
   and a poster

Where shapes can come from:
- **A drawing or a photo.** `node ../brick-check/tools/image-to-3d.mjs picture.png`
  sends it to an open image-to-3D model on Hugging Face: TripoSG (MIT), or
  InstantMesh (Apache-2.0) as a fallback. Free Spaces share GPUs and are
  sometimes down; set `HF_TOKEN` for more quota. The picture leaves your
  machine.
- **A download.** Free libraries like the Smithsonian's 3D scans (many CC0),
  NASA's models, glTF sample models, or 3D-printing sites. Check each licence.
- **A scan.** A phone scanning app exports a mesh.
- **Voxel art.** MagicaVoxel `.vox` files map almost one-to-one onto bricks.

### Parts

Anything in brick-check's catalog: bricks, plates and tiles in the usual
sizes, plus 45° slopes (studs on their top row only), and round 1x1 bricks,
plates and tiles. Slopes and round parts are drawn from their real LDraw
geometry. Parts can face 0, 90, 180 or 270 degrees.
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

- No sideways (SNOT) building, and no curved parts beyond the round 1x1s.
- The stage check uses boxes, so it can flag two actors whose boxes touch
  even when the bricks themselves wouldn't. Set pieces (room, button, door)
  aren't part of it.
- The stage check follows joints, stud by stud, but not minifig limbs.
