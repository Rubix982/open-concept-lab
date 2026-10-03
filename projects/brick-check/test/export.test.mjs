// Independent check of the exporter: read the .ldr back, place each part's
// real LDraw geometry (body only, studs excluded), and confirm no two bodies
// interpenetrate and each body lands exactly where the grid design put it.
import test from "node:test";
import assert from "node:assert/strict";
import design from "../designs/datascalar-machine.mjs";
import { toLDR } from "../lib/ldraw.mjs";
import { flatten } from "../lib/check.mjs";
import { footprint } from "../lib/parts.mjs";
import { partBox } from "../tools/ldraw-bbox.mjs";

test("exported .ldr places real part geometry without overlaps", async () => {
  const lines = toLDR(design).split("\n").filter((l) => l.startsWith("1 "));
  const grid = flatten(design);
  assert.equal(lines.length, grid.length);
  const boxes = [];
  for (const [i, l] of lines.entries()) {
    const t = l.split(/\s+/);
    const [X, Y, Z, a, , c, , , , g, , k] = t.slice(2, 14).map(Number);
    const { box } = await partBox(t[14].replace(".dat", ""));
    const lo = [box.min[0], Math.max(box.min[1], 0), box.min[2]], hi = box.max;
    const xs = [lo[0], hi[0]].flatMap((x) => [lo[2], hi[2]].map((z) => [a * x + c * z + X, g * x + k * z + Z]));
    const b = {
      min: [Math.min(...xs.map((p) => p[0])), Y + lo[1], Math.min(...xs.map((p) => p[1]))],
      max: [Math.max(...xs.map((p) => p[0])), Y + hi[1], Math.max(...xs.map((p) => p[1]))],
    };
    const p = grid[i], f = footprint(p), n = (v) => v.map((x) => Math.round(x) + 0);
    assert.deepEqual(n(b.min), n([p.x * 20, -(p.y + f.h) * 8, p.z * 20]), `part ${i} min corner`);
    assert.deepEqual(n(b.max), n([(p.x + f.w) * 20, -p.y * 8, (p.z + f.d) * 20]), `part ${i} max corner`);
    boxes.push(b);
  }
  const EPS = 0.01;
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const A = boxes[i], B = boxes[j];
    const overlap = [0, 1, 2].every((q) => A.min[q] < B.max[q] - EPS && B.min[q] < A.max[q] - EPS);
    assert.ok(!overlap, `parts ${i} and ${j} interpenetrate`);
  }
});

test("slopes land on their footprint in all four rotations", async () => {
  const { box } = await partBox("3039");
  for (const rot of [0, 90, 180, 270]) {
    const d = { title: "s", name: "s", steps: [{ note: "", parts: [{ part: "3039", color: 15, x: 3, y: 0, z: 5, rot }] }] };
    const [line] = toLDR(d).split("\n").filter((l) => l.startsWith("1 "));
    const t = line.split(/\s+/);
    const [X, , Z, a, , c, , , , g, , k] = t.slice(2, 14).map(Number);
    const xs = [box.min[0], box.max[0]].flatMap((x) => [box.min[2], box.max[2]].map((z) => [a * x + c * z + X, g * x + k * z + Z]));
    const n = (v) => Math.round(v) + 0;
    assert.deepEqual([n(Math.min(...xs.map((p) => p[0]))), n(Math.min(...xs.map((p) => p[1])))], [60, 100], `rot ${rot} min corner`);
    assert.deepEqual([n(Math.max(...xs.map((p) => p[0]))), n(Math.max(...xs.map((p) => p[1])))], [100, 140], `rot ${rot} max corner`);
  }
});
