import test from "node:test";
import assert from "node:assert/strict";
import { mirror } from "../lib/mirror.mjs";
import { physical } from "../lib/physical.mjs";
import { check } from "../lib/check.mjs";

const P = (part, x, y, z, rot = 0) => ({ part, color: 15, x, y, z, rot });

test("a mirrored model is still buildable and mirrored", () => {
  const leg = [P("3020", 0, 0, 0), P("3003", 0, 1, 0), P("3039", 0, 4, 0, 90), P("3005", 3, 1, 1)];
  const twin = mirror(leg, { axis: "x" });
  assert.deepEqual(twin.map((p) => p.x), [0, 2, 2, 0]);
  assert.equal(twin[2].rot, 270);
  assert.ok(check({ steps: [{ note: "", parts: twin }] }).ok);
});

test("mirroring twice gives back the original", () => {
  const m = [P("3039", 1, 0, 2, 0), P("3040b", 4, 0, 0, 90)];
  assert.deepEqual(mirror(mirror(m, { axis: "z" }), { axis: "z" }), m);
});

test("size is exact and weight is in the right range", () => {
  const brick = physical([P("3001", 0, 0, 0)]);
  assert.deepEqual([brick.widthMm, brick.depthMm, brick.heightMm], [32, 16, 11]);   // 31.8 x 15.8 x 11.3 mm in reality
  assert.ok(brick.grams >= 2 && brick.grams <= 3, `2x4 brick ${brick.grams} g`);   // a real one is about 2.3 g
  assert.equal(brick.estimated, true);
});
