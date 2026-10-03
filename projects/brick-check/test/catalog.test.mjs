// The catalog must agree with the real part geometry. Uses the LDraw files
// cached by tools/ldraw-bbox.mjs (fetched on first run).
import test from "node:test";
import assert from "node:assert/strict";
import { PARTS } from "../lib/parts.mjs";
import { partBox } from "../tools/ldraw-bbox.mjs";

for (const [id, s] of Object.entries(PARTS)) {
  test(`catalog ${id} matches LDraw geometry`, async () => {
    const { box } = await partBox(id);
    assert.equal(box.max[0] - box.min[0], s.w * 20, "width along X");
    assert.equal(box.max[2] - box.min[2], s.d * 20, "depth along Z");
    assert.equal(box.max[1], s.h * 8, "body height below the top face");
    assert.equal(box.min[0], -box.max[0], "origin centred in X");
    assert.equal(box.min[2], -box.max[2], "origin centred in Z");
    assert.equal(box.min[1], s.kind === "tile" ? 0 : -4, s.kind === "tile" ? "tile has no studs" : "studs rise 4 LDU");
  });
}
