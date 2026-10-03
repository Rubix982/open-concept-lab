// Brickify on shapes with known answers: whatever it produces must pass
// brick-check, and fill about the volume the shape really has.
import test from "node:test";
import assert from "node:assert/strict";
import { brickify } from "../tools/brickify.mjs";
import { check } from "../lib/check.mjs";
import { PARTS } from "../lib/parts.mjs";

// triangles of an axis-aligned box, metres, z up
function box([x0, y0, z0], [x1, y1, z1]) {
  const v = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  const f = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]];
  return f.flatMap((t) => t.flatMap((i) => v[i]));
}
function sphere([cx, cy, cz], r, n = 24) {
  const out = [], p = (i, j) => { const th = (Math.PI * i) / n, ph = (2 * Math.PI * j) / n; return [cx + r * Math.sin(th) * Math.cos(ph), cy + r * Math.sin(th) * Math.sin(ph), cz + r * Math.cos(th)]; };
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) out.push(...p(i, j), ...p(i + 1, j), ...p(i + 1, j + 1), ...p(i, j), ...p(i + 1, j + 1), ...p(i, j + 1));
  return out;
}
const mesh = (tris, colour = 15) => [Float32Array.from(tris), new Uint8Array(tris.length / 9).fill(colour)];
const passes = (parts) => {
  const r = check({ steps: [{ note: "", parts }] });
  assert.ok(r.ok, JSON.stringify(r.errors.slice(0, 3)));
  return r;
};

test("a cube comes out as a solid, buildable block of about the right volume", () => {
  // 4 cm cube, 12 plates tall: scale 0.96, so about 4.8 studs across
  const { parts, stats } = brickify(...mesh(box([0, 0, 0], [0.04, 0.04, 0.04])), { heightPlates: 12, hollow: 0 });
  passes(parts);
  const expected = (0.04 * 0.96 / 0.008) ** 2 * 12;
  assert.ok(Math.abs(stats.cells - expected) / expected < 0.45, `cells ${stats.cells} vs about ${expected.toFixed(0)}`);
  assert.equal(stats.dropped.islands + stats.dropped.unplaceable, 0);
  assert.ok(parts.every((p) => p.color === 15), "a white cube stays white");
});

test("a sphere rests on its bottom, and everything above is reachable", () => {
  const { parts, stats } = brickify(...mesh(sphere([0, 0, 0], 0.03), 4), { heightPlates: 20, hollow: 0 });
  passes(parts);
  const k = (20 * 0.0032) / 0.06, rStuds = (0.03 * k) / 0.008, rPlates = (0.03 * k) / 0.0032;
  const expected = (4 / 3) * Math.PI * rStuds * rStuds * rPlates;
  assert.ok(Math.abs(stats.cells - expected) / expected < 0.5, `cells ${stats.cells} vs about ${expected.toFixed(0)}`);
});

test("an arm within plate reach overhangs open air and is fully built", () => {
  // a 2 cm post, a 6 cm arm across the top (about 8 studs: a 2x8 plate can
  // reach from the post to its tip), and a foot under the tip so it doesn't tip
  const tris = [...box([0, 0, 0], [0.02, 0.02, 0.06]), ...box([0, 0, 0.05], [0.02, 0.06, 0.06]), ...box([0, 0, 0], [0.02, 0.06, 0.008])];
  const { parts, stats } = brickify(...mesh(tris, 25), { heightPlates: 20, hollow: 0 });
  passes(parts);
  assert.equal(stats.dropped.unplaceable + stats.dropped.islands, 0, "nothing left out");
  // the arm's lowest layer (the first one wider than the post) reaches its tip
  const right = (p) => p.x + (p.rot === 90 ? PARTS[p.part].d : PARTS[p.part].w);
  const armBottom = Math.min(...parts.filter((p) => p.y > 4 && right(p) > 3).map((p) => p.y));
  const reach = Math.max(...parts.filter((p) => p.y === armBottom).map(right));
  assert.ok(reach >= 7, `the arm's underside reaches stud ${reach}`);
});

test("an arm longer than any plate still passes, and says what it left out", () => {
  // 11 studs of arm, supported at one end only: its underside can't reach the
  // post in one layer, and the foot below stops plates going in from beneath
  const tris = [...box([0, 0, 0], [0.02, 0.02, 0.06]), ...box([0, 0, 0.05], [0.02, 0.08, 0.06]), ...box([0, 0, 0], [0.02, 0.08, 0.008])];
  const { parts, stats } = brickify(...mesh(tris, 25), { heightPlates: 20, hollow: 0 });
  passes(parts);
  assert.ok(stats.dropped.unplaceable > 0 && stats.dropped.unplaceable < parts.length * 0.15, `dropped ${stats.dropped.unplaceable} of ${parts.length}`);
});

test("hollowing leaves a shell that still passes", () => {
  const { parts, stats } = brickify(...mesh(box([0, 0, 0], [0.08, 0.08, 0.06])), { heightPlates: 18, hollow: 2 });
  passes(parts);
  const solid = brickify(...mesh(box([0, 0, 0], [0.08, 0.08, 0.06])), { heightPlates: 18, hollow: 0 }).stats.cells;
  assert.ok(stats.cells < solid, `hollow ${stats.cells} vs solid ${solid}`);
});
