# brick-check

Design a LEGO model in code, check that it can really be built, and export it.
A side build, inspired by Opus designing a buildable Microduck. The design is
only as trustworthy as its checker, so the checker is the part with tests.

First design: **Tiny DataScalar Machine**. Four chips on a green board, each
with its own memory slice, all tapped onto one yellow shared bus. 96 parts, 11 steps.

## Run

```sh
node build.mjs          # check the design, write out/datascalar-machine/
node --test test/*.test.mjs
open out/datascalar-machine/index.html   # step-by-step 3D instructions
```

No dependencies. The first test run downloads the needed part files from the
official LDraw library into `.cache/`.

## What gets checked

- **No collisions:** no two parts occupy the same space.
- **Buildable in order:** each part has something to attach to when placed and
  can be pressed into place, since nothing already built is in the way.
- **One piece:** stud connections join every part into a single component.
- **Stands up:** the centre of mass sits inside the footprint on the table.
- **Weak joints:** any part held by a single stud is flagged.

How we know the checker can be trusted:

- `test/check.test.mjs` feeds it designs that must fail, one per rule.
- `test/catalog.test.mjs` checks every part's size against real LDraw geometry.
- `test/export.test.mjs` reads the exported `.ldr` back with real geometry and
  confirms nothing overlaps.

## Outputs (`out/<design>/`)

- `index.html`: build instructions viewer (step through, orbit, parts per step).
- `<design>.ldr`: opens in BrickLink Studio, LDView, LPub3D. Studio can price it.
- `bricklink-wanted.xml`: a BrickLink wanted list. Uploading it orders nothing.
- `report.json`: the checker's verdict and numbers.

## Rough edges

- Only plain bricks, plates and tiles on a stud grid, rotated 0° or 90°. No
  slopes, hinges or sideways building.
- The physics is simple: it checks connection and balance, not how well the
  joints hold. "Buildable" means buildable according to these rules.
- Part and colour availability isn't checked. Studio or BrickLink will flag a
  combination that doesn't exist.
- **Not yet built with real bricks.** That's the real test.
