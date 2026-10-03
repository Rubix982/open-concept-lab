// The checker. A design is { steps: [{ note, parts: [{part, color, x, y, z, rot}] }] }
// on a grid: x, z in studs (min corner), y in plate heights above the table.
// Every claim brick-check makes about a design comes from here.
import { PARTS, COLORS, ROTATIONS, footprint, topStuds } from "./parts.mjs";

export function flatten(design) {
  const out = [];
  design.steps.forEach((s, step) => s.parts.forEach((p) => out.push({ ...p, step, i: out.length })));
  return out;
}

function cellsOf(p) {
  const f = footprint(p), cells = [];
  for (let x = p.x; x < p.x + f.w; x++)
    for (let z = p.z; z < p.z + f.d; z++)
      for (let y = p.y; y < p.y + f.h; y++) cells.push([x, y, z]);
  return cells;
}

export function check(design) {
  const parts = flatten(design);
  const errors = [], warnings = [];
  const err = (rule, msg, part) => errors.push({ rule, msg, part });

  // --- vocabulary
  for (const p of parts) {
    if (!PARTS[p.part]) err("vocabulary", `unknown part ${p.part}`, p.i);
    if (!(p.color in COLORS)) err("vocabulary", `unknown colour ${p.color}`, p.i);
    if (!ROTATIONS.includes(p.rot)) err("vocabulary", `rotation must be one of ${ROTATIONS.join(", ")}`, p.i);
    if (![p.x, p.y, p.z].every(Number.isInteger) || p.y < 0) err("vocabulary", `off-grid position`, p.i);
  }
  if (errors.length) return { ok: false, errors, warnings, parts };

  // --- collisions
  const occ = new Map();
  for (const p of parts) for (const c of cellsOf(p)) {
    const k = c.join(",");
    if (occ.has(k)) err("collision", `part ${p.i} overlaps part ${occ.get(k)} at ${k}`, p.i);
    else occ.set(k, p.i);
  }

  // --- connections: a stud on P's top entering Q's bottom
  const studs = new Map(); // "a-b" -> count, a below b
  const add = (a, b) => { const k = a + "-" + b; studs.set(k, (studs.get(k) || 0) + 1); };
  for (const p of parts) {
    const top = p.y + footprint(p).h;
    for (const [x, z] of topStuds(p)) {
      const q = occ.get(`${x},${top},${z}`);
      if (q !== undefined && parts[q].y === top) add(p.i, q);
    }
  }
  const edges = [...studs].map(([k, n]) => { const [a, b] = k.split("-").map(Number); return { below: a, above: b, studs: n }; });
  const conn = parts.map(() => 0);
  for (const e of edges) { conn[e.below] += e.studs; conn[e.above] += e.studs; }

  // --- one piece
  const parent = parts.map((_, i) => i);
  const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  for (const e of edges) parent[find(e.below)] = find(e.above);
  const comps = new Set(parts.map((p) => find(p.i)));
  if (comps.size > 1) err("one-piece", `design falls apart into ${comps.size} separate pieces`, null);

  // --- buildable in the order given
  const placed = new Set();
  const maxY = Math.max(...parts.map((p) => p.y + footprint(p).h));
  for (const p of parts) {
    const f = footprint(p);
    const below = edges.filter((e) => e.above === p.i && placed.has(e.below));
    const above = edges.filter((e) => e.below === p.i && placed.has(e.above));
    if (p.y > 0 && !below.length && !above.length)
      err("buildable", `step ${p.step + 1}: part ${p.i} (${PARTS[p.part].name}) has nothing to attach to when placed`, p.i);
    const blocked = (y0, y1) => {
      for (let x = p.x; x < p.x + f.w; x++) for (let z = p.z; z < p.z + f.d; z++)
        for (let y = y0; y < y1; y++) { const q = occ.get(`${x},${y},${z}`); if (q !== undefined && placed.has(q)) return true; }
      return false;
    };
    if (below.length || p.y === 0) {
      if (blocked(p.y + f.h, maxY + 1))
        err("buildable", `step ${p.step + 1}: part ${p.i} (${PARTS[p.part].name}) can't be pressed down — something is already built above it`, p.i);
    } else if (above.length && blocked(0, p.y)) {
      err("buildable", `step ${p.step + 1}: part ${p.i} (${PARTS[p.part].name}) can't be pushed up into place — something is already built below it`, p.i);
    }
    placed.add(p.i);
  }

  // --- stands up: centre of mass over the table contact area
  let m = 0, cx = 0, cz = 0;
  for (const p of parts) {
    const f = footprint(p), v = f.w * f.d * f.h;
    m += v; cx += v * (p.x + f.w / 2); cz += v * (p.z + f.d / 2);
  }
  cx /= m; cz /= m;
  const pts = [];
  for (const p of parts.filter((p) => p.y === 0)) {
    const f = footprint(p);
    pts.push([p.x, p.z], [p.x + f.w, p.z], [p.x, p.z + f.d], [p.x + f.w, p.z + f.d]);
  }
  const hull = convexHull(pts);
  const margin = hull.length >= 3 ? insideMargin(hull, [cx, cz]) : -Infinity;
  if (!(margin > 0)) err("stands-up", `centre of mass (${cx.toFixed(2)}, ${cz.toFixed(2)}) is not over the footprint`, null);

  // --- weak joints
  parts.forEach((p, i) => { if (conn[i] === 1) warnings.push({ rule: "weak-joint", msg: `part ${i} (${PARTS[p.part].name}) is held by a single stud`, part: i }); });

  return {
    ok: errors.length === 0, errors, warnings, parts, edges,
    stats: {
      parts: parts.length,
      steps: design.steps.length,
      studConnections: edges.reduce((s, e) => s + e.studs, 0),
      pieces: comps.size,
      centreOfMass: [+cx.toFixed(3), +cz.toFixed(3)],
      comMarginStuds: +margin.toFixed(3),
      height: maxY,
    },
  };
}

function convexHull(points) {
  const p = [...new Map(points.map((q) => [q.join(","), q])).values()].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) return p;
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [], upper = [];
  for (const q of p) { while (lower.length >= 2 && cross(lower.at(-2), lower.at(-1), q) <= 0) lower.pop(); lower.push(q); }
  for (const q of [...p].reverse()) { while (upper.length >= 2 && cross(upper.at(-2), upper.at(-1), q) <= 0) upper.pop(); upper.push(q); }
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

// Distance from point to the nearest hull edge; negative if outside (CCW hull).
function insideMargin(hull, [x, y]) {
  let best = Infinity;
  for (let i = 0; i < hull.length; i++) {
    const [ax, ay] = hull[i], [bx, by] = hull[(i + 1) % hull.length];
    const len = Math.hypot(bx - ax, by - ay);
    const signed = ((bx - ax) * (y - ay) - (by - ay) * (x - ax)) / len;
    best = Math.min(best, signed);
  }
  return best;
}
