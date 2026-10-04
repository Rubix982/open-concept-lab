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
