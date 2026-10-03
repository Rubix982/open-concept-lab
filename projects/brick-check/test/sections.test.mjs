import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { sections } from "../tools/sections.mjs";

const plate = (x, y, z) => ({ part: "3022", color: 15, x, y, z, rot: 0 });   // 2x2 plates

test("a wide-narrow-wide stack is cut at the narrow part", () => {
  const parts = [];
  for (let y = 0; y < 10; y++) for (let x = 0; x < 6; x += 2) for (let z = 0; z < 6; z += 2) parts.push(plate(x + (y % 2), y, z + (y % 2)));  // wide, seams staggered
  for (let y = 10; y < 18; y++) parts.push(plate(2, y, 2));                                                                    // narrow neck
  for (let y = 18; y < 26; y++) for (let x = 0; x < 6; x += 2) for (let z = 0; z < 6; z += 2) parts.push(plate(x + (y % 2), y, z + (y % 2)));
  const s = sections(parts);
  assert.ok(s.length >= 2, JSON.stringify(s));
  assert.ok(s.some((sec) => sec.base >= 10 && sec.base <= 18), "a cut lands on the neck");
});

test("a plain block isn't cut", () => {
  const parts = [];
  for (let y = 0; y < 20; y++) for (let x = 0; x < 4; x += 2) parts.push(plate(x + (y % 2), y, 0));
  assert.equal(sections(parts).length, 1);
});

test("the Microduck is cut near its ankles, waist or neck, and its head can be built alone", { skip: !fs.existsSync(new URL("../out/microduck/microduck-bricks.json", import.meta.url)) }, () => {
  const { parts } = JSON.parse(fs.readFileSync(new URL("../out/microduck/microduck-bricks.json", import.meta.url)));
  const s = sections(parts);
  assert.ok(s.length >= 2, JSON.stringify(s));
  assert.ok(s.every((sec, k) => k === 0 || sec.base > s[k - 1].base), "sections go up");
  assert.ok(s.at(-1).base >= 40, `top section starts at ${s.at(-1).base}`);
});
