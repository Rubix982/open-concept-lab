// Checked against an outside source: element IDs printed in the Microduck
// booklet's parts inventory (page 138), which came from LEGO via Rebrickable.
import test from "node:test";
import assert from "node:assert/strict";
import { availability, rebrickablePart, colourName, ensureCatalogue } from "../lib/availability.mjs";
import { PARTS, COLORS } from "../lib/parts.mjs";

test("element IDs from the Microduck booklet are found", async () => {
  const booklet = [
    ["3009", 0, "300926"], ["3002", 0, "300226"], ["3024", 0, "302426"], ["3023b", 0, "302326"],
    ["3623", 0, "362326"], ["3710", 0, "371026"], ["3005", 72, "4211098"], ["3004", 72, "4211088"],
    ["3001", 72, "4211085"], ["3022", 72, "4211094"],
  ];
  const r = await availability(booklet.map(([part, color]) => ({ part, color })));
  booklet.forEach(([part, color, id], i) => assert.ok(r.lines[i].elementIds.includes(id), `${part} in ${color} should include ${id}, got ${r.lines[i].elementIds}`));
});

test("every catalogue part maps to a Rebrickable part", async () => {
  await ensureCatalogue();
  for (const id of Object.keys(PARTS)) assert.ok(rebrickablePart(id), `no Rebrickable part for ${id}`);
});

test("our colour names agree with Rebrickable's", async () => {
  await ensureCatalogue();
  for (const [code, [name]] of Object.entries(COLORS)) assert.equal(colourName(+code), name);
});

test("a combination LEGO never made is flagged", async () => {
  // a white 1x1 brick exists; the same brick in a colour code Rebrickable doesn't list does not
  const r = await availability([{ part: "3005", color: 15 }, { part: "3005", color: 9999 }]);
  assert.equal(r.lines[0].exists, true);
  assert.equal(r.lines[1].exists, false);
  assert.equal(r.ok, false);
});

test("fitToCatalogue swaps a colour LEGO never made for the nearest one it did", async () => {
  const { fitToCatalogue } = await import("../lib/availability.mjs");
  const { parts, changes } = await fitToCatalogue([{ part: "3032", color: 29, x: 0, y: 0, z: 0, rot: 0 }, { part: "3005", color: 15, x: 0, y: 1, z: 0, rot: 0 }]);
  const r = await availability(parts);
  assert.equal(r.ok, true, JSON.stringify(r.missing));
  assert.equal(parts[1].color, 15, "parts that exist are left alone");
  assert.equal(changes.length, 1);
});
