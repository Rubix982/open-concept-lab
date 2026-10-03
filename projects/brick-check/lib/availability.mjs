// Is each part made in the colour a design asks for? Checked against
// Rebrickable's public catalogue (rebrickable.com/downloads), which lists
// every LEGO element: a part in a colour, with its LEGO element ID — the
// number LEGO's Pick a Brick sells by. Same source the Microduck booklet used.
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";
import { PARTS, COLORS } from "./parts.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(here, "..", ".cache", "rebrickable");
const FILES = ["colors", "elements", "parts"];

export async function ensureCatalogue() {
  fs.mkdirSync(dir, { recursive: true });
  for (const f of FILES) {
    const file = path.join(dir, `${f}.csv.gz`);
    if (fs.existsSync(file)) continue;
    const res = await fetch(`https://cdn.rebrickable.com/media/downloads/${f}.csv.gz`);
    if (!res.ok) throw new Error(`couldn't download Rebrickable ${f}: ${res.status}`);
    fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
  }
}

let cat = null;
function load() {
  if (cat) return cat;
  const rows = (f) => zlib.gunzipSync(fs.readFileSync(path.join(dir, `${f}.csv.gz`))).toString().split("\n").slice(1).filter(Boolean);
  const parts = new Set(rows("parts").map((l) => l.split(",")[0]));
  const colors = new Map(rows("colors").map((l) => { const [id, name] = l.split(","); return [+id, name]; }));
  const elements = new Map();      // "part|colour" -> [element ids]
  for (const l of rows("elements")) {
    const [el, part, color] = l.split(",");
    const k = `${part}|${color}`;
    if (!elements.has(k)) elements.set(k, []);
    elements.get(k).push(el);
  }
  return (cat = { parts, colors, elements });
}

// Rebrickable mostly uses LDraw numbers, but not always (3023b is 3023), and
// a part's colours can be split across its variants (white 2x2 round plates
// are under 4032, not 4032b). These are the numbers to try, in order.
// Sibling variants (4032a/4032b: design revisions of one part) count too.
function candidates(id) {
  const base = id.replace(/[a-z]$/, ""), { parts } = load();
  const siblings = "abcdef".split("").map((l) => base + l).filter((c) => parts.has(c));
  return [...new Set([id, PARTS[id]?.bl, base, ...siblings].filter(Boolean))];
}
export function rebrickablePart(id, color) {
  const { parts, elements } = load();
  const known = candidates(id).filter((c) => parts.has(c));
  if (color != null) return known.find((c) => elements.has(`${c}|${color}`)) || known[0] || null;
  return known[0] || null;
}

// For every part/colour in a list of parts: is it a real element, and what
// are its LEGO element IDs (newest first)?
export async function availability(parts) {
  await ensureCatalogue();
  const { elements, colors } = load();
  const lines = new Map();
  for (const p of parts) {
    const k = `${p.part}|${p.color}`;
    if (!lines.has(k)) lines.set(k, { part: p.part, color: p.color, qty: 0 });
    lines.get(k).qty++;
  }
  const out = [...lines.values()].map((l) => {
    const rb = rebrickablePart(l.part, l.color);
    const ids = rb ? (elements.get(`${rb}|${l.color}`) || []) : [];
    return {
      ...l, rebrickable: rb, colorName: colors.get(l.color) ?? COLORS[l.color]?.[0],
      exists: ids.length > 0, elementIds: [...ids].sort((a, b) => Number(b) - Number(a)),
    };
  });
  return { ok: out.every((l) => l.exists), lines: out, missing: out.filter((l) => !l.exists) };
}

export function colourName(code) { return load().colors.get(code); }

// Recolour any part LEGO never made in its colour to the nearest colour (in
// perceptual Lab distance) that the same part does come in. Geometry is
// untouched, so a design that passed check() still does. Returns the new
// parts and what changed.
export async function fitToCatalogue(parts) {
  await ensureCatalogue();
  const { elements } = load();
  const has = (part, color) => { const rb = rebrickablePart(part, color); return rb && elements.has(`${rb}|${color}`); };
  const lab = (hex) => {
    const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v > 0.04045 ? ((v + 0.055) / 1.055) ** 2.4 : v / 12.92));
    const [x, y, z] = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]].map((r, i) => (r[0] * c[0] + r[1] * c[1] + r[2] * c[2]) / [0.9505, 1, 1.089][i]);
    const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
    return [116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))];
  };
  const changes = new Map();
  const out = parts.map((p) => {
    if (has(p.part, p.color)) return p;
    const from = lab(COLORS[p.color][2]);
    const best = Object.keys(COLORS).map(Number).filter((c) => has(p.part, c))
      .sort((a, b) => dist(lab(COLORS[a][2]), from) - dist(lab(COLORS[b][2]), from))[0];
    if (best === undefined) return p;                 // nothing to swap to; availability() will still flag it
    const k = `${PARTS[p.part].name}: ${COLORS[p.color][0]} → ${COLORS[best][0]}`;
    changes.set(k, (changes.get(k) || 0) + 1);
    return { ...p, color: best };
  });
  return { parts: out, changes: [...changes].map(([what, n]) => `${n}× ${what}`) };
}
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
