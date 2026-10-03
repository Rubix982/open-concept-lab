// The catalog must agree with the real part geometry. Uses the LDraw files
// cached by tools/ldraw-bbox.mjs (fetched on first run).
import test from "node:test";
import assert from "node:assert/strict";
import { PARTS } from "../lib/parts.mjs";
import { partBox } from "../tools/ldraw-bbox.mjs";
import { studCells } from "../tools/ldraw-studs.mjs";

for (const [id, s] of Object.entries(PARTS)) {
  test(`catalog ${id} matches LDraw geometry`, async () => {
    const { box } = await partBox(id);
    const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 0.01, `${msg}: ${a} vs ${b}`);
    const [cx, cz] = s.center || [0, 0];
    near(box.max[0] - box.min[0], s.w * 20, "width along X");
    near(box.max[2] - box.min[2], s.d * 20, "depth along Z");
    near(box.max[1], s.h * 8, "body height below the top face");
    near((box.min[0] + box.max[0]) / 2, cx, "footprint centre in X");
    near((box.min[2] + box.max[2]) / 2, cz, "footprint centre in Z");
    const expected = s.studs ?? (s.kind === "tile" ? [] : Array.from({ length: s.w * s.d }, (_, n) => [Math.floor(n / s.d), n % s.d]));
    assert.deepEqual(await studCells(id), [...expected].sort((a, b) => a[0] - b[0] || a[1] - b[1]), "stud cells");
    assert.equal(box.min[1], expected.length ? -4 : 0, expected.length ? "studs rise 4 LDU" : "no studs on top");
  });
}
