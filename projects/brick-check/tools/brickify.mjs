// Brickify: turn a triangle mesh into a plate-built model that brick-check
// passes. The mesh is sampled into a grid of studs (across) by plates (up),
// filled, optionally hollowed, then each layer is packed into catalog plates
// and the plates are put in an order you could actually build them in.
//
// Units: input in metres, z up (MuJoCo / CAD convention). Output parts use
// brick-check's grid: x and z in studs, y in plates. 1 stud = 8 mm,
// 1 plate = 3.2 mm, so the grid is 2.5x finer vertically than across.
import { PARTS } from "../lib/parts.mjs";

const STUD = 0.008, PLATE = 0.0032;

// Plates from the catalog, both orientations, largest first.
const PLATES = Object.entries(PARTS)
  .filter(([, s]) => s.kind === "plate" && !s.mesh)
  .flatMap(([id, s]) => (s.w === s.d ? [{ id, w: s.w, d: s.d, rot: 0 }] : [{ id, w: s.w, d: s.d, rot: 0 }, { id, w: s.d, d: s.w, rot: 90 }]))
  .sort((a, b) => b.w * b.d - a.w * a.d || Math.max(b.w, b.d) - Math.max(a.w, a.d));

// ---- 1. sample the surface into the grid -----------------------------------
function voxelize(tri, colors, heightPlates) {
  let min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < tri.length; i++) { const k = i % 3; if (tri[i] < min[k]) min[k] = tri[i]; if (tri[i] > max[k]) max[k] = tri[i]; }
  const k = (heightPlates * PLATE) / (max[2] - min[2]);          // real-world scale factor
  // grid x <- mesh y, grid z <- -mesh x (mesh +x is the front, grid z = 0 is the front), grid y <- mesh z
  const toGrid = (x, y, z) => [(y - min[1]) * k / STUD, (z - min[2]) * k / PLATE, (max[0] - x) * k / STUD];
  // half-open: a model spans exactly heightPlates layers, and a face lying on
  // a cell boundary doesn't spill into an extra, one-cell-thin layer
  const NX = Math.max(1, Math.ceil((max[1] - min[1]) * k / STUD - 1e-6)), NY = heightPlates, NZ = Math.max(1, Math.ceil((max[0] - min[0]) * k / STUD - 1e-6));
  const idx = (x, y, z) => (y * NZ + z) * NX + x;
  const surface = new Uint8Array(NX * NY * NZ);
  const votes = new Map();                                         // cell -> {colour: count}
  const mark = (g, c) => {
    const x = Math.min(NX - 1, Math.floor(g[0])), y = Math.min(NY - 1, Math.floor(g[1])), z = Math.min(NZ - 1, Math.floor(g[2]));
    const i = idx(x, y, z);
    surface[i] = 1;
    let v = votes.get(i); if (!v) votes.set(i, (v = {}));
    v[c] = (v[c] || 0) + 1;
  };
  for (let t = 0; t < tri.length / 9; t++) {
    const a = toGrid(tri[t * 9], tri[t * 9 + 1], tri[t * 9 + 2]);
    const b = toGrid(tri[t * 9 + 3], tri[t * 9 + 4], tri[t * 9 + 5]);
    const c = toGrid(tri[t * 9 + 6], tri[t * 9 + 7], tri[t * 9 + 8]);
    // sample finely enough that no cell the triangle crosses is skipped
    const span = Math.max(...[0, 1, 2].map((q) => Math.max(Math.abs(a[q] - b[q]), Math.abs(b[q] - c[q]), Math.abs(a[q] - c[q]))));
    const n = Math.max(1, Math.ceil(span * 2));
    for (let i = 0; i <= n; i++) for (let j = 0; j <= n - i; j++) {
      const u = i / n, v = j / n, w = 1 - u - v;
      mark([a[0] * w + b[0] * u + c[0] * v, a[1] * w + b[1] * u + c[1] * v, a[2] * w + b[2] * u + c[2] * v], colors[t]);
    }
  }
  return { NX, NY, NZ, idx, surface, votes, scale: k };
}

// ---- 2. fill: everything the outside air can't reach is solid -------------
// Flooding from outside is robust to meshes that aren't watertight: small gaps
// close up at brick resolution, and separate shells just merge.
function fill({ NX, NY, NZ, idx, surface }) {
  const outside = new Uint8Array(NX * NY * NZ), queue = [];
  const push = (x, y, z) => {
    if (x < 0 || y < 0 || z < 0 || x >= NX || y >= NY || z >= NZ) return;
    const i = idx(x, y, z);
    if (outside[i] || surface[i]) return;
    outside[i] = 1; queue.push(x, y, z);
  };
  for (let x = 0; x < NX; x++) for (let y = 0; y < NY; y++) { push(x, y, 0); push(x, y, NZ - 1); }
  for (let z = 0; z < NZ; z++) for (let y = 0; y < NY; y++) { push(0, y, z); push(NX - 1, y, z); }
  for (let x = 0; x < NX; x++) for (let z = 0; z < NZ; z++) { push(x, NY - 1, z); push(x, 0, z); }
  for (let q = 0; q < queue.length; q += 3) {
    const x = queue[q], y = queue[q + 1], z = queue[q + 2];
    push(x + 1, y, z); push(x - 1, y, z); push(x, y + 1, z); push(x, y - 1, z); push(x, y, z + 1); push(x, y, z - 1);
  }
  const solid = new Uint8Array(NX * NY * NZ);
  for (let i = 0; i < solid.length; i++) solid[i] = outside[i] ? 0 : 1;
  return { solid, outside };
}

// ---- 3. colour, and hollow the inside ------------------------------------
// Surface cells take their majority triangle colour. Cells the outside can't
// see are "any colour" (null), so the packer can use them to bridge seams.
function colourAndHollow(g, solid, outside, hollow) {
  const { NX, NY, NZ, idx, votes } = g, N = NX * NY * NZ;
  const depth = new Int16Array(N).fill(-1), queue = [];
  const nb = (x, y, z, f) => { f(x + 1, y, z); f(x - 1, y, z); f(x, y + 1, z); f(x, y - 1, z); f(x, y, z + 1); f(x, y, z - 1); };
  const inb = (x, y, z) => x >= 0 && y >= 0 && z >= 0 && x < NX && y < NY && z < NZ;
  for (let y = 0; y < NY; y++) for (let z = 0; z < NZ; z++) for (let x = 0; x < NX; x++) {
    const i = idx(x, y, z);
    if (!solid[i]) continue;
    let exposed = false;
    nb(x, y, z, (a, b, c) => { if (!inb(a, b, c) || outside[idx(a, b, c)]) exposed = true; });
    if (exposed) { depth[i] = 0; queue.push(x, y, z); }
  }
  for (let q = 0; q < queue.length; q += 3) {
    const x = queue[q], y = queue[q + 1], z = queue[q + 2], d = depth[idx(x, y, z)];
    nb(x, y, z, (a, b, c) => { if (inb(a, b, c)) { const j = idx(a, b, c); if (solid[j] && depth[j] < 0) { depth[j] = d + 1; queue.push(a, b, c); } } });
  }
  const colour = new Int16Array(N).fill(-1);       // -1: empty, -2: any colour
  for (let i = 0; i < N; i++) {
    if (!solid[i]) continue;
    if (hollow > 0 && depth[i] > hollow) continue;            // hollowed out
    if (depth[i] === 0) {
      const v = votes.get(i);
      if (v) colour[i] = +Object.entries(v).sort((p, q) => q[1] - p[1])[0][0];
      else colour[i] = -3;                                     // exposed filler: takes a neighbour's colour below
    } else colour[i] = -2;
  }
  // exposed cells with no triangle of their own borrow the nearest surface colour
  for (let pass = 0; pass < 6; pass++) {
    for (let y = 0; y < NY; y++) for (let z = 0; z < NZ; z++) for (let x = 0; x < NX; x++) {
      const i = idx(x, y, z);
      if (colour[i] !== -3) continue;
      let found = -3;
      nb(x, y, z, (a, b, c) => { if (found === -3 && inb(a, b, c) && colour[idx(a, b, c)] >= 0) found = colour[idx(a, b, c)]; });
      if (found !== -3) colour[i] = found;
    }
  }
  for (let i = 0; i < N; i++) if (colour[i] === -3) colour[i] = -2;
  return colour;
}

// ---- 4. pack each layer into plates ---------------------------------------
// A plate covers same-coloured cells (any-colour cells match anything).
// Overhang cells (nothing directly beneath) are covered first, by a plate that
// also reaches a supported cell when one is in range, so it has studs below
// to sit on. Odd and even layers prefer opposite orientations so seams cross.
function pack(g, colour, seed) {
  const { NX, NY, NZ, idx } = g, parts = [];
  let recoloured = 0;
  for (let y = 0; y < NY; y++) {
    const used = new Uint8Array(NX * NZ), at = (x, z) => colour[idx(x, y, z)];
    const filled = (x, z) => x >= 0 && z >= 0 && x < NX && z < NZ && at(x, z) !== -1;
    const supported = (x, z) => y === 0 || colour[idx(x, y - 1, z)] !== -1;
    const order = PLATES.slice().sort((a, b) => (b.w * b.d - a.w * a.d) || ((y + seed) % 2 ? a.w - b.w : b.w - a.w));
    // can plate p sit with its min corner at (x0, z0)? returns its colour, or
    // null. With `mixed`, cells of other colours are allowed (they get recoloured).
    function fits(p, x0, z0, mixed = false) {
      let col = -2;
      for (let x = x0; x < x0 + p.w; x++) for (let z = z0; z < z0 + p.d; z++) {
        if (!filled(x, z) || used[x * NZ + z]) return null;
        const c = at(x, z);
        if (c >= 0) { if (col >= 0 && col !== c && !mixed) return null; if (col < 0) col = c; }
      }
      return col;
    }
    function place(p, x0, z0, col) {
      for (let x = x0; x < x0 + p.w; x++) for (let z = z0; z < z0 + p.d; z++) {
        used[x * NZ + z] = 1;
        if (col >= 0 && at(x, z) >= 0 && at(x, z) !== col) recoloured++;
      }
      parts.push({ part: p.id, color: col >= 0 ? col : 72, x: x0, y, z: z0, rot: p.rot });
    }
    const touchesSupport = (p, x0, z0) => { for (let x = x0; x < x0 + p.w; x++) for (let z = z0; z < z0 + p.d; z++) if (supported(x, z)) return true; return false; };
    // pass 1: overhang cells, each covered by the biggest plate that also
    // reaches support. Same colour if possible; otherwise the smallest plate
    // that reaches support, in the overhang's colour (a few cells recoloured
    // beats a plate with nothing to hold it).
    // farthest from support first: the longest reaches get first pick of the
    // supported cells, before nearer overhangs use them up
    const dist = new Int16Array(NX * NZ).fill(-1), q = [];
    for (let x = 0; x < NX; x++) for (let z = 0; z < NZ; z++) if (filled(x, z) && supported(x, z)) { dist[x * NZ + z] = 0; q.push(x, z); }
    for (let h = 0; h < q.length; h += 2) {
      const x = q[h], z = q[h + 1];
      for (const [a, b] of [[x + 1, z], [x - 1, z], [x, z + 1], [x, z - 1]]) if (filled(a, b) && dist[a * NZ + b] < 0) { dist[a * NZ + b] = dist[x * NZ + z] + 1; q.push(a, b); }
    }
    const overhang = [];
    for (let x = 0; x < NX; x++) for (let z = 0; z < NZ; z++) if (filled(x, z) && !supported(x, z)) overhang.push([x, z]);
    overhang.sort((a, b) => dist[b[0] * NZ + b[1]] - dist[a[0] * NZ + a[1]]);
    for (const [x, z] of overhang) {
      if (used[x * NZ + z]) continue;
      let best = null;
      for (const mixed of [false, true]) {
        const tries = mixed ? order.slice().reverse() : order;
        for (const p of tries) {
          for (let ox = 0; ox < p.w && !best; ox++) for (let oz = 0; oz < p.d && !best; oz++) {
            const x0 = x - ox, z0 = z - oz, col = fits(p, x0, z0, mixed);
            if (col !== null && touchesSupport(p, x0, z0)) best = { p, x0, z0, col: at(x, z) >= 0 ? at(x, z) : col };
          }
          if (best) break;
        }
        if (best) break;
      }
      if (best) place(best.p, best.x0, best.z0, best.col);
    }
    // pass 2: everything else, largest plates first, scanning from a shifted start
    const sx = (seed * 3 + y) % 2, sz = (seed + y * 2) % 3;
    for (let xi = 0; xi < NX; xi++) for (let zi = 0; zi < NZ; zi++) {
      const x = (xi + sx) % NX, z = (zi + sz) % NZ;
      if (!filled(x, z) || used[x * NZ + z]) continue;
      let done = false;
      for (const p of order) {
        for (let ox = 0; ox < p.w && !done; ox++) for (let oz = 0; oz < p.d && !done; oz++) {
          const col = fits(p, x - ox, z - oz);
          if (col !== null) { place(p, x - ox, z - oz, col); done = true; }
        }
        if (done) break;
      }
    }
  }
  parts.recoloured = recoloured;
  return parts;
}

// ---- 5. connectivity and a buildable order --------------------------------
// Plates connect where they overlap on neighbouring layers (every plate has
// studs on every cell).
function footprint(p) { const s = PARTS[p.part]; return p.rot === 90 ? [s.d, s.w] : [s.w, s.d]; }
function links(parts) {
  const byLayer = new Map();
  parts.forEach((p, i) => { (byLayer.get(p.y) || byLayer.set(p.y, []).get(p.y)).push(i); });
  const cellOwner = new Map();
  parts.forEach((p, i) => { const [w, d] = footprint(p); for (let x = p.x; x < p.x + w; x++) for (let z = p.z; z < p.z + d; z++) cellOwner.set(`${x},${p.y},${z}`, i); });
  const below = parts.map(() => new Set()), above = parts.map(() => new Set());
  parts.forEach((p, i) => {
    const [w, d] = footprint(p);
    for (let x = p.x; x < p.x + w; x++) for (let z = p.z; z < p.z + d; z++) {
      const j = cellOwner.get(`${x},${p.y + 1},${z}`);
      if (j !== undefined) { above[i].add(j); below[j].add(i); }
    }
  });
  return { below, above, cellOwner };
}
function components(parts, { below, above }) {
  const comp = parts.map(() => -1); let n = 0;
  for (let s = 0; s < parts.length; s++) {
    if (comp[s] >= 0) continue;
    const st = [s]; comp[s] = n;
    while (st.length) { const i = st.pop(); for (const j of [...below[i], ...above[i]]) if (comp[j] < 0) { comp[j] = n; st.push(j); } }
    n++;
  }
  return { comp, n };
}
// Bottom-up by layer. A plate with nothing under it waits until a plate above
// it is down, then goes in from below — allowed only while nothing already
// placed sits under it (brick-check's rule). Plates that can't be placed are
// returned as `stuck`.
function order(parts, L) {
  const placed = new Uint8Array(parts.length), out = [], occupied = new Set();
  const columnsBelowClear = (p) => {
    const [w, d] = footprint(p);
    for (let x = p.x; x < p.x + w; x++) for (let z = p.z; z < p.z + d; z++) for (let y = 0; y < p.y; y++) if (occupied.has(`${x},${y},${z}`)) return false;
    return true;
  };
  const put = (i) => { placed[i] = 1; out.push(parts[i]); const p = parts[i], [w, d] = footprint(p); for (let x = p.x; x < p.x + w; x++) for (let z = p.z; z < p.z + d; z++) occupied.add(`${x},${p.y},${z}`); };
  const ids = parts.map((_, i) => i).sort((a, b) => parts[a].y - parts[b].y);
  let waiting = [];
  for (const i of ids) {
    const p = parts[i];
    if (p.y === 0 || [...L.below[i]].some((j) => placed[j])) {
      put(i);
      // anything waiting under this plate can now go in from below
      for (let changed = true; changed;) {
        changed = false;
        waiting = waiting.filter((k) => {
          if ([...L.above[k]].some((j) => placed[j]) && columnsBelowClear(parts[k])) { put(k); changed = true; return false; }
          return true;
        });
      }
    } else waiting.push(i);
  }
  return { ordered: out, stuck: waiting };
}

// A region that hangs from above (a thigh joined to the body but not to the
// shin) would have to go in from underneath, which the parts below block.
// Where the gap under such a plate is small, fill it with a strut so the
// region rests on what's below, the way a builder would. Returns cells added.
function addStruts(g, colour, maxGap) {
  const { idx } = g;
  let added = 0;
  for (let round = 0; round < 6; round++) {
    const parts = pack(g, colour, 0), L = links(parts), { stuck } = order(parts, L);
    const roots = stuck.filter((i) => !L.below[i].size);
    if (!roots.length) break;
    let changed = 0;
    for (const i of roots) {
      const p = parts[i], [w, d] = footprint(p);
      for (let x = p.x; x < p.x + w; x++) for (let z = p.z; z < p.z + d; z++) {
        for (let k = 2; k <= maxGap + 1 && p.y - k >= 0; k++) {
          if (colour[idx(x, p.y - k, z)] === -1) continue;
          for (let y = p.y - k + 1; y < p.y; y++) { colour[idx(x, y, z)] = p.color; changed++; }
          break;
        }
      }
    }
    if (!changed) break;
    added += changed;
  }
  return added;
}

export function brickify(triangles, colors, { heightPlates = 60, hollow = 2, seeds = 6, maxGap = 4 } = {}) {
  const g = voxelize(triangles, colors, heightPlates);
  const { solid, outside } = fill(g);
  const colour = colourAndHollow(g, solid, outside, hollow);
  const struts = maxGap > 0 ? addStruts(g, colour, maxGap) : 0;
  const cells = colour.reduce((s, c) => s + (c !== -1 ? 1 : 0), 0);

  // try a few seam patterns; keep the one with the most plates in its main piece
  let best = null;
  for (let seed = 0; seed < seeds; seed++) {
    let parts = pack(g, colour, seed);
    const recoloured = parts.recoloured;
    const dropped = { islands: 0, unplaceable: 0 };
    for (let round = 0; round < 8; round++) {
      const L = links(parts), { comp, n } = components(parts, L);
      // keep the piece that stands on the ground with the most plates; drop the rest
      const size = new Array(n).fill(0), grounded = new Array(n).fill(false);
      parts.forEach((p, i) => { size[comp[i]]++; if (p.y === 0) grounded[comp[i]] = true; });
      let main = -1; for (let c = 0; c < n; c++) if (grounded[c] && (main < 0 || size[c] > size[main])) main = c;
      const kept = parts.filter((_, i) => comp[i] === main);
      dropped.islands += parts.length - kept.length;
      const L2 = links(kept), { ordered, stuck } = order(kept, L2);
      if (!stuck.length) { parts = ordered; break; }
      dropped.unplaceable += stuck.length;
      const bad = new Set(stuck.map((i) => kept[i]));
      parts = kept.filter((p) => !bad.has(p));
    }
    const score = parts.length - 3 * (dropped.islands + dropped.unplaceable);
    if (!best || score > best.score) best = { parts, dropped, seed, score, recoloured };
  }

  const xs = best.parts.flatMap((p) => { const [w] = footprint(p); return [p.x, p.x + w]; });
  const zs = best.parts.flatMap((p) => { const [, d] = footprint(p); return [p.z, p.z + d]; });
  return {
    parts: best.parts,
    stats: {
      plates: best.parts.length, cells, seed: best.seed,
      dropped: best.dropped, recolouredCells: best.recoloured, strutCells: struts,
      layers: new Set(best.parts.map((p) => p.y)).size,
      sizeStuds: [Math.max(...xs) - Math.min(...xs), Math.max(...zs) - Math.min(...zs)],
      heightPlates: Math.max(...best.parts.map((p) => p.y)) + 1,
      sizeCm: [((Math.max(...xs) - Math.min(...xs)) * 0.8).toFixed(1), ((Math.max(...zs) - Math.min(...zs)) * 0.8).toFixed(1), ((Math.max(...best.parts.map((p) => p.y)) + 1) * 0.32).toFixed(1)],
      colours: Object.fromEntries(Object.entries(best.parts.reduce((m, p) => ((m[p.color] = (m[p.color] || 0) + 1), m), {}))),
    },
  };
}
