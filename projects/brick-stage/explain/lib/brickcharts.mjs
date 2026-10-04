// Brick charts: data in, a real LEGO model out.
//
// Each builder returns { parts, anchors, size }:
//   parts    real catalogue parts { part, color, x, y, z, rot } in build order,
//            on a two-layer bonded base so the whole chart is one piece.
//            build.mjs runs them through brick-check (collisions, studs, one
//            piece) and lists the parts, like any brick-stage model.
//   anchors  named points [x, y, z] (studs, plates, studs) the 2D layer can
//            pin labels, values and arrows to: "bar3", "cell:2:14", "top"...
//   size     the footprint and height, for framing the camera.
// The blueprint player builds the parts on camera, part by part, in order.
import { P } from "../../lib/director.mjs";

// LEGO colour codes (LDraw = Rebrickable)
export const LEGO = {
  black: 0, blue: 1, green: 2, darkTurquoise: 3, red: 4, darkPink: 5, brightGreen: 10, yellow: 14, white: 15,
  tan: 19, orange: 25, magenta: 26, lime: 27, darkTan: 28, brightPink: 29, mediumLavender: 30, lightGray: 71,
  darkGray: 72, mediumBlue: 73, darkPurple: 85, brightLightOrange: 191, brightLightBlue: 212,
};
// sequential ramps for heat maps, low → high
export const RAMPS = {
  green: [LEGO.darkGray, LEGO.darkTurquoise, LEGO.green, LEGO.brightGreen, LEGO.lime, LEGO.yellow],
  violet: [LEGO.darkGray, LEGO.darkPurple, LEGO.magenta, LEGO.mediumLavender, LEGO.brightPink, LEGO.white],
  heat: [LEGO.darkGray, LEGO.darkPurple, LEGO.red, LEGO.orange, LEGO.brightLightOrange, LEGO.yellow],
  blue: [LEGO.darkGray, LEGO.blue, LEGO.mediumBlue, LEGO.brightLightBlue, LEGO.white],
};
const rampColor = (ramp, v) => ramp[Math.max(0, Math.min(ramp.length - 1, Math.round(v * (ramp.length - 1))))];

// plates by size class: [length, part] for 4-, 2- and 1-stud-wide plates
const PLATES = {
  4: [[12, "3029"], [10, "3030"], [6, "3032"], [4, "3031"]],
  2: [[12, "2445"], [8, "3034"], [6, "3795"], [4, "3020"], [3, "3021"], [2, "3022"]],
  1: [[8, "3460"], [6, "3666"], [4, "3710"], [3, "3623"], [2, "3023b"], [1, "3024"]],
};
// Lay plates `width` studs wide end to end from `a` to `b` along x (rot 0) or
// along z (rot 90), at the other coordinate `at`, height y. `first` caps the
// first plate's length, so neighbouring runs don't share seams.
function run(out, color, a, b, at, y, width, axis, first = 0) {
  let pos = a, startRun = true;
  while (pos < b) {
    let opts = PLATES[width].filter(([len]) => len <= b - pos);
    if (startRun && first) opts = opts.filter(([len]) => len <= first);
    if (!opts.length) { // nothing this wide fits: two narrower runs
      const half = width / 2;
      run(out, color, pos, b, at, y, half, axis, first); run(out, color, pos, b, at + half, y, half, axis, first);
      return;
    }
    const [len, part] = opts[0];
    out.push(axis === "x" ? P(part, color, pos, y, at) : P(part, color, at, y, pos, 90));
    pos += len; startRun = false;
  }
}
const lanes = (total, widths = [4, 2, 1]) => { const out = []; let at = 0; while (at < total) { const w = widths.find((k) => k <= total - at); out.push([at, w]); at += w; } return out; };
// A w × d base in two cross-laid layers, like plywood: the bottom runs left to
// right with each row's seams shifted, the top runs front to back across every
// bottom row, so the whole base is one piece (brick-check confirms it).
export function base(w, d, color = LEGO.darkGray) {
  // even sizes only: a one-stud leftover strip on both layers would line up
  // and nothing would bridge it
  w += w % 2; d += d % 2;
  const out = [];
  lanes(d).forEach(([z, width], j) => run(out, color, 0, w, z, 0, width, "x", j % 2 ? 6 : 0));
  // top columns start one stud in, so their seams sit on odd studs and the
  // bottom's (even-length plates) on even ones: every seam is bridged
  [[0, 1], ...lanes(w - 1, [2, 1]).map(([x, k]) => [x + 1, k])].forEach(([x, width], i) => run(out, color, 0, d, x, 1, width, "z", i % 2 ? 6 : 0));
  return out;
}

/** Bars of 2×2 bricks. values: numbers; o.max sets the full height (plates).
 *  Heights are rounded to whole plates; a bar is bricks, topped up with plates. */
export function barChart(values, o = {}) {
  const n = values.length, gap = o.gap ?? 2, bw = 2, margin = 2;
  const maxV = o.maxValue ?? Math.max(...values), maxPlates = o.maxPlates ?? 30;
  const colors = o.colors || values.map(() => LEGO.mediumBlue);
  const W = margin * 2 + n * bw + (n - 1) * gap, D = o.depth ?? 6;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const z = Math.floor((D - bw) / 2);
  values.forEach((v, i) => {
    const x = margin + i * (bw + gap), plates = Math.max(1, Math.round((v / maxV) * maxPlates));
    let y = 2;
    for (let b = 0; b < Math.floor(plates / 3); b++, y += 3) parts.push(P("3003", colors[i], x, y, z));
    for (let k = 0; k < plates % 3; k++, y += 1) parts.push(P("3022", colors[i], x, y, z));
    anchors[`bar${i}`] = [x + 1, y, z + 1];
    anchors[`foot${i}`] = [x + 1, 2, z + bw + 0.6];
  });
  return { parts, anchors, size: [W, Math.max(...values.map((v) => Math.round((v / maxV) * maxPlates))) + 2, D] };
}

/** A heat map of 1×1 columns: colour from a ramp, height from the value.
 *  values[row][col] in 0..1; rows run front to back, columns left to right. */
export function heatGrid(values, o = {}) {
  const rows = values.length, cols = values[0].length, margin = o.margin ?? 1;
  const ramp = o.ramp || RAMPS.heat, maxH = o.maxPlates ?? 6;
  const W = cols + margin * 2, D = rows + margin + (rows + margin * 2 > 12 ? 0 : margin);
  const parts = base(W, D, o.base ?? LEGO.black), anchors = {};
  // build column by column, so the map sweeps in left to right
  for (let c = 0; c < cols; c++) for (let r = 0; r < rows; r++) {
    const v = Math.max(0, Math.min(1, values[r][c])), col = rampColor(ramp, v);
    const h = o.flat ? 0 : Math.round(v * maxH), x = margin + c, z = margin + r;
    for (let k = 0; k < h; k++) parts.push(P("3024", col, x, 2 + k, z));
    parts.push(P("3070b", col, x, 2 + h, z));
    anchors[`cell:${r}:${c}`] = [x + 0.5, 3 + h, z + 0.5];
  }
  for (let r = 0; r < rows; r++) anchors[`row${r}`] = [margin - 0.6, 2, margin + r + 0.5];
  for (let c = 0; c < cols; c++) anchors[`col${c}`] = [margin + c + 0.5, 2, margin + rows + 0.6];
  return { parts, anchors, size: [W, maxH + 3, D] };
}

/** Columns of 1×1 round bricks, one per value, each capped with a round tile:
 *  a lollipop chart; draw the line between the tops in 2D. o.log for log values. */
export function columns(values, o = {}) {
  const n = values.length, gap = o.gap ?? 1, margin = 1, maxPlates = o.maxPlates ?? 24;
  const tx = (v) => (o.log ? Math.max(0, Math.log10(Math.max(v, o.min ?? 1e-5)) - Math.log10(o.min ?? 1e-5)) / -Math.log10(o.min ?? 1e-5) : v / (o.maxValue ?? Math.max(...values)));
  const W = margin * 2 + n + (n - 1) * gap, D = 3;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const colors = o.colors || values.map(() => LEGO.brightLightBlue);
  values.forEach((v, i) => {
    const x = margin + i * (1 + gap), z = 1, plates = Math.max(0, Math.round(tx(v) * maxPlates));
    let y = 2;
    for (let b = 0; b < Math.floor(plates / 3); b++, y += 3) parts.push(P("3062b", colors[i], x, y, z));
    for (let k = 0; k < plates % 3; k++, y += 1) parts.push(P("6141", colors[i], x, y, z));
    parts.push(P("98138", o.cap?.[i] ?? LEGO.white, x, y, z));
    anchors[`top${i}`] = [x + 0.5, y + 1, z + 0.5];
    anchors[`foot${i}`] = [x + 0.5, 2, z + 1.6];
  });
  return { parts, anchors, size: [W, maxPlates + 3, D] };
}

/** A diagram of brick blocks. nodes: [{ id, x, z, w, d, h (bricks), color }]
 *  (w × d from 2×2, 2×4); arrows between them are drawn in 2D from the
 *  anchors "<id>" (top centre) and "<id>.front". */
export function blocks(nodes, o = {}) {
  const W = o.width ?? Math.max(...nodes.map((n) => n.x + n.w)) + 2, D = o.depth ?? Math.max(...nodes.map((n) => n.z + n.d)) + 2;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const part = (w, d) => (w === 4 && d === 2 ? "3001" : w === 2 && d === 2 ? "3003" : w === 2 && d === 1 ? "3004" : w === 1 && d === 1 ? "3005" : null);
  for (const n of nodes) {
    const id = part(n.w, n.d);
    if (!id) throw new Error(`blocks: no ${n.w}×${n.d} brick`);
    let y = 2;
    for (let k = 0; k < (n.h ?? 1); k++, y += 3) parts.push(P(id, n.color ?? LEGO.mediumBlue, n.x, y, n.z));
    if (n.cap) { parts.push(P(n.w === 4 ? "2431" : "3068b", n.cap, n.x, y, n.z)); y += 1; } // a tile on top
    anchors[n.id] = [n.x + n.w / 2, y, n.z + n.d / 2];
    anchors[`${n.id}.front`] = [n.x + n.w / 2, 2 + ((n.h ?? 1) * 3) / 2, n.z + n.d + 0.1];
  }
  return { parts, anchors, size: [W, Math.max(...nodes.map((n) => (n.h ?? 1) * 3)) + 3, D] };
}

// ---------------------------------------------------------------------------
// More charts. Shared helpers first.

// fill `plates` plate-heights of a w × d column at (x, y, z) with bricks, then
// plates: 2×2 → 3003/3022, 1×1 → 3005/3024. Returns the new top y.
function column(parts, kind, color, x, y, z, plates) {
  const [brick, plate] = kind === "1x1" ? ["3005", "3024"] : ["3003", "3022"];
  for (let b = 0; b < Math.floor(plates / 3); b++, y += 3) parts.push(P(brick, color, x, y, z));
  for (let k = 0; k < plates % 3; k++, y += 1) parts.push(P(plate, color, x, y, z));
  return y;
}
const finite = (v) => (Number.isFinite(v) ? v : 0);
const maxOf = (vals, fallback = 1) => { const m = Math.max(0, ...vals.map(finite)); return m > 0 ? m : fallback; };

/** Stacked bars: series[i] is one bar's segments, bottom to top; colours per
 *  segment index. Anchors: bar<i> (top), seg<i>:<k> (front face, mid-segment), foot<i>. */
export function stackedBars(series, o = {}) {
  const n = series.length, gap = o.gap ?? 2, bw = 2, margin = 2, maxPlates = o.maxPlates ?? 30;
  const totals = series.map((s) => s.reduce((a, v) => a + Math.max(0, finite(v)), 0));
  const maxT = o.maxValue ?? maxOf(totals);
  const colors = o.colors || [LEGO.mediumBlue, LEGO.orange, LEGO.brightGreen, LEGO.red, LEGO.yellow, LEGO.mediumLavender];
  const W = margin * 2 + n * bw + (n - 1) * gap, D = o.depth ?? 6;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const z = Math.floor((D - bw) / 2);
  let top = 0;
  series.forEach((segs, i) => {
    const x = margin + i * (bw + gap);
    let y = 2;
    segs.forEach((v, k) => {
      const plates = v > 0 ? Math.max(1, Math.round((v / maxT) * maxPlates)) : 0;
      const y0 = y;
      y = column(parts, "2x2", colors[k % colors.length], x, y, z, plates);
      anchors[`seg${i}:${k}`] = [x + 1, (y0 + y) / 2, z + bw + 0.1];
    });
    if (y === 2) y = column(parts, "2x2", LEGO.lightGray, x, y, z, 1); // an empty bar still shows
    anchors[`bar${i}`] = [x + 1, y, z + 1];
    anchors[`foot${i}`] = [x + 1, 2, z + bw + 0.6];
    top = Math.max(top, y);
  });
  return { parts, anchors, size: [W, top, D], scale: { maxValue: maxT, maxPlates } };
}

/** Grouped bars: groups[g][k] — one cluster of touching 2×2 bars per group,
 *  colour by k. Anchors: bar<g>:<k> (top), group<g> (foot of the cluster). */
export function groupedBars(groups, o = {}) {
  const g = groups.length, k = Math.max(1, ...groups.map((s) => s.length)), bw = 2, gap = o.gap ?? 3, margin = 2, maxPlates = o.maxPlates ?? 30;
  const maxV = o.maxValue ?? maxOf(groups.flat());
  const colors = o.colors || [LEGO.mediumBlue, LEGO.orange, LEGO.brightGreen, LEGO.red, LEGO.yellow];
  const W = margin * 2 + g * k * bw + (g - 1) * gap, D = o.depth ?? 6;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const z = Math.floor((D - bw) / 2);
  let top = 0;
  groups.forEach((vals, gi) => {
    const gx = margin + gi * (k * bw + gap);
    vals.forEach((v, ki) => {
      const x = gx + ki * bw, plates = Math.max(1, Math.round((Math.max(0, finite(v)) / maxV) * maxPlates));
      const y = column(parts, "2x2", colors[ki % colors.length], x, 2, z, plates);
      anchors[`bar${gi}:${ki}`] = [x + 1, y, z + 1];
      top = Math.max(top, y);
    });
    anchors[`group${gi}`] = [gx + (vals.length * bw) / 2, 2, z + bw + 0.6];
  });
  return { parts, anchors, size: [W, top, D], scale: { maxValue: maxV, maxPlates } };
}

/** A number line from min to max: a white 1-wide plate line, a tile under each
 *  tick, and a round-brick marker for each mark ({ value, color, height }).
 *  Anchors: tick<i> (in front of the tick), mark<i> (top of the marker), start, end. */
export function numberLine(min, max, o = {}) {
  const L = o.length ?? 30, margin = 2, D = 4, zLine = 1, zTick = 2;
  const W = L + margin * 2;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  const pos = (v) => margin + Math.round(((finite(v) - min) / (max - min || 1)) * (L - 1));
  run(parts, o.line ?? LEGO.white, margin, margin + L, zLine, 2, 1, "x");
  const ticks = o.ticks ?? [min, max];
  ticks.forEach((v, i) => {
    const x = pos(v);
    parts.push(P("3070b", o.tick ?? LEGO.lightGray, x, 2, zTick));
    anchors[`tick${i}`] = [x + 0.5, 2, zTick + 1.6];
  });
  const height = new Map(); // stack markers that land on the same stud
  (o.marks ?? []).forEach((m, i) => {
    const x = pos(m.value), y0 = height.get(x) ?? 3;
    let y = y0;
    for (let b = 0; b < (m.height ?? 1); b++, y += 3) parts.push(P("3062b", m.color ?? LEGO.orange, x, y, zLine));
    height.set(x, y);
    anchors[`mark${i}`] = [x + 0.5, y, zLine + 0.5];
  });
  anchors.start = [margin, 3, zLine + 0.5];
  anchors.end = [margin + L, 3, zLine + 0.5];
  return { parts, anchors, size: [W, Math.max(3, ...height.values()), D] };
}

/** A scatter plot on posts: x runs left to right, y is the post height, and
 *  points that share a column step back in depth. points: [[x, y, colourIndex?]].
 *  Each point is a coloured round plate on a light grey 1×1 stem.
 *  Anchors: pt<i> (the head), xmin, xmax. */
export function scatter(points, o = {}) {
  const L = o.length ?? 24, margin = 1, maxPlates = o.maxPlates ?? 18;
  const xMax = o.xMax ?? maxOf(points.map((p) => p[0])), yMax = o.yMax ?? maxOf(points.map((p) => p[1]));
  const colors = o.colors || [LEGO.orange, LEGO.mediumBlue, LEGO.brightGreen, LEGO.red];
  const used = new Map(); // x → next free z row
  const cells = points.map(([x, y, c]) => {
    const sx = margin + Math.round((Math.max(0, finite(x)) / xMax) * (L - 1));
    const z = used.get(sx) ?? 1; used.set(sx, z + 1);
    return { sx, z, h: Math.round((Math.max(0, finite(y)) / yMax) * maxPlates), c: c ?? 0 };
  });
  const D = Math.max(3, ...cells.map((c) => c.z + 2)), W = L + margin * 2;
  const parts = base(W, D, o.base ?? LEGO.darkGray), anchors = {};
  cells.forEach(({ sx, z, h, c }, i) => {
    const y = column(parts, "1x1", o.stem ?? LEGO.lightGray, sx, 2, z, h);
    parts.push(P("6141", colors[c % colors.length], sx, y, z));
    anchors[`pt${i}`] = [sx + 0.5, y + 1, z + 0.5];
  });
  anchors.xmin = [margin, 2, D - 0.4];
  anchors.xmax = [margin + L, 2, D - 0.4];
  return { parts, anchors, size: [W, maxPlates + 3, D] };
}

/** A waffle chart: a 10 × 10 grid of 1×1 tiles, one per percent, filled row by
 *  row in category order. counts: a percentage (one number) or counts per
 *  category (scaled to 100). Anchors: cat<k> (middle of its tiles), cell<n>. */
export function waffle(counts, o = {}) {
  const raw = Array.isArray(counts) ? counts : [counts, 100 - counts];
  const total = raw.reduce((a, v) => a + Math.max(0, finite(v)), 0) || 1;
  // largest-remainder rounding, so the tiles always add up to 100
  const exact = raw.map((v) => (Math.max(0, finite(v)) / total) * 100), whole = exact.map(Math.floor);
  let left = 100 - whole.reduce((a, v) => a + v, 0);
  exact.map((v, i) => [v - whole[i], i]).sort((a, b) => b[0] - a[0]).forEach(([, i]) => { if (left > 0) { whole[i]++; left--; } });
  const colors = o.colors || (Array.isArray(counts) ? [LEGO.mediumBlue, LEGO.orange, LEGO.brightGreen, LEGO.red, LEGO.yellow] : [LEGO.orange, LEGO.darkGray]);
  const margin = 1, W = 10 + margin * 2, D = 10 + margin * 2;
  const parts = base(W, D, o.base ?? LEGO.black), anchors = {};
  let n = 0;
  whole.forEach((count, k) => {
    const sum = [0, 0];
    for (let j = 0; j < count; j++, n++) {
      const x = margin + (n % 10), z = margin + Math.floor(n / 10);
      parts.push(P("3070b", colors[k % colors.length], x, 2, z));
      anchors[`cell${n}`] = [x + 0.5, 3, z + 0.5];
      sum[0] += x + 0.5; sum[1] += z + 0.5;
    }
    if (count) anchors[`cat${k}`] = [sum[0] / count, 3, sum[1] / count];
  });
  return { parts, anchors, size: [W, 3, D], counts: whole };
}

/** A matrix (attention-style): values[r][c] in 0..1 as coloured tiles, flat by
 *  default (o.raise for height), labelled on both axes in 2D.
 *  Anchors: cell:<r>:<c>, row<r> (left edge), col<c> (front edge). */
export function matrix(values, o = {}) {
  const rows = values.length, cols = Math.max(1, ...values.map((r) => r.length)), margin = 1;
  const ramp = o.ramp || RAMPS.blue, maxH = o.raise ? (o.maxPlates ?? 4) : 0;
  const W = cols + margin * 2, D = rows + margin * 2;
  const parts = base(W, D, o.base ?? LEGO.black), anchors = {};
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const v = Math.max(0, Math.min(1, finite(values[r][c]))), col = rampColor(ramp, v);
    const h = Math.round(v * maxH), x = margin + c, z = margin + r;
    for (let k = 0; k < h; k++) parts.push(P("3024", col, x, 2 + k, z));
    parts.push(P("3070b", col, x, 2 + h, z));
    anchors[`cell:${r}:${c}`] = [x + 0.5, 3 + h, z + 0.5];
  }
  for (let r = 0; r < rows; r++) anchors[`row${r}`] = [margin - 0.4, 2, margin + r + 0.5];
  for (let c = 0; c < cols; c++) anchors[`col${c}`] = [margin + c + 0.5, 2, margin + rows + 0.4];
  return { parts, anchors, size: [W, maxH + 3, D] };
}

/** A graph: node blocks, and edges laid as 1-wide tile roads on the base
 *  (Manhattan routing: along x from the source, then along z into the target).
 *  nodes: [{ id, x, z, w, d, h, color, cap }] as in blocks(); edges: [{ from, to, color, route }]
 *  (route "bus": down, across, down — o.route sets it for every edge).
 *  Anchors: <id>, <id>.front, edge<i>:a / :turn / :b / :mid (on the road). */
export function graph(nodes, edges, o = {}) {
  const chart = blocks(nodes, o), parts = chart.parts, anchors = chart.anchors;
  const [W, , D] = chart.size;
  // cells under node blocks are taken; roads go around them by stopping at their edge
  const taken = new Set();
  for (const n of nodes) for (let x = n.x; x < n.x + n.w; x++) for (let z = n.z; z < n.z + n.d; z++) taken.add(`${x},${z}`);
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const road = new Set();
  const lay = (x, z, color) => {
    const k = `${x},${z}`;
    if (taken.has(k) || road.has(k) || x < 0 || z < 0 || x >= W + (W % 2) || z >= D + (D % 2)) return;
    road.add(k); parts.push(P("3070b", color, x, 2, z));
  };
  edges.forEach((e, i) => {
    const a = byId[e.from], b = byId[e.to];
    if (!a || !b) throw new Error(`graph: edge ${e.from} → ${e.to} names a missing node`);
    const ax = a.x + Math.floor(a.w / 2), az = a.z + Math.floor(a.d / 2);
    const bx = b.x + Math.floor(b.w / 2), bz = b.z + Math.floor(b.d / 2);
    const color = e.color ?? o.road ?? LEGO.white, cells = [];
    let turn = [bx, az];
    if ((e.route ?? o.route) === "bus") { // down from the source, across, down into the target: tidy trees
      const mz = Math.round((az + bz) / 2);
      for (let z = az; z !== mz; z += Math.sign(mz - az)) cells.push([ax, z]);
      for (let x = ax; x !== bx; x += Math.sign(bx - ax)) cells.push([x, mz]);
      for (let z = mz; z !== bz; z += Math.sign(bz - mz)) cells.push([bx, z]);
      turn = [bx, mz];
    } else {
      for (let x = ax; x !== bx; x += Math.sign(bx - ax)) cells.push([x, az]);
      for (let z = az; z !== bz; z += Math.sign(bz - az)) cells.push([bx, z]);
    }
    cells.push([bx, bz]);
    for (const [x, z] of cells) lay(x, z, color);
    const free = cells.filter(([x, z]) => !taken.has(`${x},${z}`));
    const mid = free[Math.floor(free.length / 2)] || cells[Math.floor(cells.length / 2)];
    anchors[`edge${i}:a`] = [ax + 0.5, 3, az + 0.5];
    anchors[`edge${i}:turn`] = [turn[0] + 0.5, 3, turn[1] + 0.5];
    anchors[`edge${i}:b`] = [bx + 0.5, 3, bz + 0.5];
    anchors[`edge${i}:mid`] = [mid[0] + 0.5, 3, mid[1] + 0.5];
  });
  return { ...chart, parts };
}

/** A tree laid out top-down as a graph: root { id, label?, color?, children: [...] }.
 *  Leaves are spread evenly, parents centred over their children; depth runs
 *  front to back. Anchors as graph(). */
export function tree(root, o = {}) {
  const nodes = [], edges = [], nw = o.nodeW ?? 2, nd = 2, xGap = o.xGap ?? 3, zGap = o.zGap ?? 4;
  let leaf = 0;
  const place = (n, depth) => {
    const kids = n.children || [];
    const xs = kids.map((k) => place(k, depth + 1));
    const x = kids.length ? Math.round((xs[0] + xs[xs.length - 1]) / 2) : 1 + (leaf++) * (nw + xGap);
    nodes.push({ id: n.id, x, z: 1 + depth * (nd + zGap), w: nw, d: nd, h: n.h ?? 1, color: n.color ?? (o.colors?.[depth] ?? LEGO.mediumBlue), cap: n.cap });
    for (const k of kids) edges.push({ from: n.id, to: k.id, color: o.road });
    return x;
  };
  place(root, 0);
  return graph(nodes, edges, { route: "bus", ...o });
}

/** A y axis: a 1×1 column at the chart's left edge, a white plate at each tick
 *  height and dark plates between, capped with a tile. ticks: plate heights
 *  above the base, or values with { maxValue, maxPlates } (barChart's scale).
 *  Returns the chart with the column added and anchors ytick<i>. */
export function axes(chart, o = {}) {
  const parts = chart.parts.slice(), anchors = { ...chart.anchors };
  const [, , D] = chart.size;
  const x = o.x ?? 0, z = o.z ?? Math.max(0, Math.floor(D / 2) - 1);
  const scale = o.maxValue != null ? o : chart.scale;
  const toPlates = (t) => (scale ? Math.round((t / scale.maxValue) * scale.maxPlates) : t);
  const ticks = (o.ticks ?? []).map(toPlates);
  const top = Math.max(1, ...ticks) + 1;
  const tickSet = new Set(ticks);
  for (let k = 0; k < top; k++) parts.push(P("3024", tickSet.has(k + 1) ? LEGO.white : (o.color ?? LEGO.darkGray), x, 2 + k, z));
  parts.push(P("3070b", o.color ?? LEGO.darkGray, x, 2 + top, z));
  ticks.forEach((h, i) => { anchors[`ytick${i}`] = [x, 2 + h - 0.5, z + 0.5]; });
  return { ...chart, parts, anchors, size: [chart.size[0], Math.max(chart.size[1], top + 3), chart.size[2]] };
}
