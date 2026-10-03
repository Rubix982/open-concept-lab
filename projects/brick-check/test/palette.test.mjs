import test from "node:test";
import assert from "node:assert/strict";
import { nearestColour, toLegoColours } from "../lib/palette.mjs";

test("colours land on the LEGO colour a person would pick", () => {
  assert.equal(nearestColour([255, 255, 255]), 15);          // white
  assert.equal(nearestColour([200, 20, 10]), 4);             // red
  assert.equal(nearestColour([160, 165, 170]), 71);          // light bluish grey, not pink
  assert.equal(nearestColour([120, 30, 20]), 320);           // dark red
  assert.equal(nearestColour([90, 150, 60]), 10);            // a mid green
});

test("a limited palette is respected", () => {
  assert.equal(nearestColour([200, 20, 10], [0, 15]), 0);
  assert.deepEqual(toLegoColours(new Uint8Array([255, 255, 255, 5, 5, 5]), [0, 15]), [15, 0]);
});

test("clustering keeps a shaded yellow yellow", async () => {
  const { clusterToLego } = await import("../lib/palette.mjs");
  // 300 yellows from bright to shadowed, plus a few orange and black triangles
  const rgb = [];
  for (let i = 0; i < 300; i++) { const s = 1 - (i / 300) * 0.45; rgb.push(Math.round(242 * s), Math.round(205 * s), Math.round(55 * s)); }
  for (let i = 0; i < 30; i++) rgb.push(254, 138, 24);
  for (let i = 0; i < 10; i++) rgb.push(10, 10, 12);
  const codes = clusterToLego(new Uint8Array(rgb), 3);
  const yellows = codes.slice(0, 300);
  assert.ok(yellows.filter((c) => c === 14).length > 200, `most shades stay Yellow: ${[...new Set(yellows)]}`);
  assert.equal(codes[310], 25);
  assert.equal(codes[335], 0);
});
