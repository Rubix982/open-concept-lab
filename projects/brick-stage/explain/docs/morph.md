# Morph: one model rebuilds itself into another

```js
import { barChart, LEGO } from "../lib/brickcharts.mjs";
const A = barChart([0.58, 0.28, 0.03, 0.03], { colors, gap: 3 });
const B = barChart([0.42, 0.43, 0.98, 0.98], { colors, gap: 3 });

s.morph("bars", A, B, { az: -26, el: 22, dist: 46 });   // builds A part by part
s.together((g) => {
  g.set("bars", { morph: 1 }, { dur: 4200 });           // A → B
  g.sfx("morph", { dur: 4200 });                         // clicks + whoosh
});
```

A chain: `s.morph("bars", null, null, { models: [A, B, C] })`, then
`s.set("bars", { morph: 1 })`, later `{ morph: 2 }`. `morph` is a number
from 0 to n − 1, so it tweens like anything else. Tween `az`, `el` and
`dist` alongside it to move the camera during the morph.

How parts move:
- **Matching:** parts are matched from one model to the next, same part
  and colour first, then the same part in another colour (it changes colour
  mid-flight), nearest first.
- **Matched parts:** they lift, fly an arc and settle. They're staggered
  left to right and bottom to top, so a growing bar fills like a cascade.
  Parts that don't move (usually the base) stay put.
- **Leftovers:** parts the next model doesn't need lift off and shrink away
  early. New parts drop in late.
- **Checking:** every model in the chain goes through brick-check at build
  time (`plugins/morph.build.mjs`), and the build fails if any model isn't
  buildable.

Anchors for pinning 2D things:
- `"a:bar0"`, `"b:bar0"` or `"m2:bar0"` pin to a point on one model.
- A plain `"bar0"` follows whichever model the morph is nearer: model 0
  until `morph` passes 0.5, then model 1.

Morphs read best when the models share a layout, as with bar charts of the
same width and colours. Then most parts match and you see bricks migrate.
Between different chart kinds (bars → round columns) few parts match, so
most of the morph is parts leaving and arriving.

See `scripts/cap-morph.mjs` (cache-router: median wait → cache hits → busiest GPU).
