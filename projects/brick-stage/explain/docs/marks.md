# Math, code and marks

`lib/plugins/marks.js` (drawing) and `lib/actions/marks.mjs` (script verbs).
Try it: `node explain/build.mjs cap-marks`, then open `out/cap-marks/index.html`.

## Math

```js
s.math("attn", String.raw`\mathrm{softmax}\!\left(\frac{QK^{\top}}{\color{#ff7a59}{\sqrt{d_k}}}\right)V`, { x: 960, y: 400, size: 74 });
```

Typeset by MathJax 3 (SVG, loaded from jsdelivr before the player starts) and
written on left to right with a soft edge and a pen line. `size` is the em size
in pixels; `color` is a theme colour; colour a part with `\color{#hex}{…}`.
Offline it shows the TeX source instead of failing.

## Code

```js
s.code("go", source, { lang: "go", x: 120, y: 190, size: 21, title: "file.go", focus: [3, 4] });
s.focus("go", [8, 9]);   // the focus bar slides there, other lines dim
```

A framed panel with line numbers and a small built-in highlighter for `go`,
`js` and `python` (keywords, strings, numbers, comments, types). Lines type
themselves on.

## Counters

```js
s.count("t", 580, 28, { format: "ms", label: "first token, median", dur: 2000 });
```

Formats: `int`, `comma`, `ms`, `pct` (0..1), `x`, `s`, `fixed1`, `fixed2`;
`prefix`/`suffix` for anything else.

## Marks

`underline`, `strike`, `circle`, `highlight`, `brace` (side: below | above |
left | right, with `label`), `arrowTo(id, [fromX, fromY], { label, bend })`.
Each draws itself on. Place a mark with a box `{ x, y, w, h }` (x, y = centre)
or an `anchor`:

| anchor | means |
| ------ | ----- |
| `{ id, line }` | a line of a code panel (1-based) |
| `{ id, fx, fy }` | a point inside another object's bounds (fractions); give `w`, `h` for the mark's size |
| `{ id }` | around another object (math, code, counter) |
| `{ obj, at }` / `{ obj, col, row }` | a point on a 3D stage, as for text and notes |

Bounds come from objects of this plugin (math, code, counter); a mark must be
created after the object it points at.
