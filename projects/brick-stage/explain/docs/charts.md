# Brick charts

`explain/lib/brickcharts.mjs`: data in, a real LEGO model out. Every builder returns
`{ parts, anchors, size }`. The parts sit on a two-layer base that is one piece at any
size, and `explain/build.mjs` runs each model through brick-check. Use a chart in a
script with `s.bricks(id, chart, { az, el, dist })`. Pin 2D text, notes and paths to its
anchors with `{ anchor: { obj: id, at: "<name>" } }`.

| Builder | Data | Model | Anchors |
| ------- | ---- | ----- | ------- |
| `barChart(values)` | numbers | 2×2 brick columns | `bar<i>`, `foot<i>` |
| `stackedBars(series)` | `series[i]` = one bar's segments, bottom up | 2×2 columns, one colour per segment | `bar<i>`, `seg<i>:<k>` (front face), `foot<i>` |
| `groupedBars(groups)` | `groups[g][k]` | touching 2×2 columns per group | `bar<g>:<k>`, `group<g>` |
| `heatGrid(values)` | `values[r][c]` in 0..1 | 1×1 columns, colour + height | `cell:<r>:<c>`, `row<r>`, `col<c>` |
| `matrix(values, { raise })` | `values[r][c]` in 0..1, rows may be ragged | flat (or raised) 1×1 tiles | `cell:<r>:<c>`, `row<r>`, `col<c>` |
| `columns(values, { log })` | numbers | round-brick lollipops | `top<i>`, `foot<i>` |
| `scatter(points)` | `[[x, y, colour?]]` | coloured round plates on grey stems; shared columns step back | `pt<i>`, `xmin`, `xmax` |
| `numberLine(min, max, { ticks, marks })` | tick values; marks `{ value, color, height }` | white plate line, tick tiles, round-brick markers | `tick<i>`, `mark<i>`, `start`, `end` |
| `waffle(p or counts)` | a percentage, or counts per category | 10 × 10 tiles, one per hundredth (largest-remainder rounding) | `cat<k>`, `cell<n>`; `.counts` |
| `blocks(nodes)` | `[{ id, x, z, w, d, h, color, cap }]` | brick blocks | `<id>`, `<id>.front` |
| `graph(nodes, edges)` | blocks + `[{ from, to, color, route }]` | blocks joined by 1-wide tile roads (`route: "bus"` for down–across–down) | as blocks, plus `edge<i>:a`, `:turn`, `:b`, `:mid` |
| `tree(root)` | `{ id, children: [...] }` | a graph laid out by depth, bus-routed | as graph |
| `axes(chart, { ticks })` | tick heights in plates, or values with the chart's `scale` | a 1×1 plate column at the left, white plates at the ticks | `ytick<i>` |

`base(w, d)` is exported too: odd sizes are rounded up to even. It is one piece at every
size from 2×2 to 40×26, which `test/brickcharts.test.mjs` checks along with every builder:

```bash
node --test test/brickcharts.test.mjs
node explain/build.mjs cap-charts      # all eight newer charts on real data
```
