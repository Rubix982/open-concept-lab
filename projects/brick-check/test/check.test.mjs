// The checker is the instrument, so it is tested on designs that must fail.
import test from "node:test";
import assert from "node:assert/strict";
import { check } from "../lib/check.mjs";

const P = (part, x, y, z, rot = 0, color = 15) => ({ part, color, x, y, z, rot });
const one = (...parts) => ({ steps: [{ note: "", parts }] });
const rules = (r) => r.errors.map((e) => e.rule);

test("a simple stack passes", () => {
  const r = check(one(P("3020", 0, 0, 0), P("3001", 0, 1, 0), P("3068b", 1, 4, 0)));
  assert.ok(r.ok, JSON.stringify(r.errors));
  assert.equal(r.stats.studConnections, 8 + 4);
});

test("overlapping parts are a collision", () => {
  const r = check(one(P("3001", 0, 0, 0), P("3001", 2, 1, 0)));
  assert.ok(rules(r).includes("collision"));
});

test("a part floating in the air is caught", () => {
  const r = check(one(P("3001", 0, 0, 0), P("3001", 0, 6, 0)));
  assert.ok(rules(r).includes("buildable"));
  assert.ok(rules(r).includes("one-piece"));
});

test("plates side by side with nothing bridging them fall apart", () => {
  const r = check(one(P("3020", 0, 0, 0), P("3020", 4, 0, 0)));
  assert.deepEqual(rules(r), ["one-piece"]);
});

test("the same plates bridged by a third are one piece", () => {
  const r = check(one(P("3020", 0, 0, 0), P("3020", 4, 0, 0), P("3020", 2, 1, 0)));
  assert.ok(r.ok, JSON.stringify(r.errors));
});

test("nothing sticks to the top of a tile", () => {
  const r = check(one(P("3020", 0, 0, 0), P("3068b", 0, 1, 0), P("3003", 0, 2, 0)));
  assert.ok(rules(r).includes("one-piece"));
});

test("a brick can't be jammed under an overhang that is already built", () => {
  const r = check(one(
    P("3020", 0, 0, 0),          // base
    P("3003", 0, 1, 0),          // pillar
    P("3020", 0, 4, 0),          // overhang across x 0..4
    P("3003", 2, 1, 0),          // fills the gap — too late
  ));
  assert.deepEqual(rules(r), ["buildable"]);
});

test("the same parts in a buildable order pass", () => {
  const r = check(one(P("3020", 0, 0, 0), P("3003", 0, 1, 0), P("3003", 2, 1, 0), P("3020", 0, 4, 0)));
  assert.ok(r.ok, JSON.stringify(r.errors));
});

test("a heavy cantilever tips over", () => {
  const r = check(one(
    P("3003", 0, 0, 0), P("2445", 0, 3, 0),
    P("3003", 10, 4, 0), P("3003", 10, 7, 0), P("3003", 10, 10, 0),
  ));
  assert.ok(rules(r).includes("stands-up"));
});

test("a single-stud joint is flagged", () => {
  const r = check(one(P("3003", 0, 0, 0), P("3004", 1, 3, 1)));
  assert.ok(r.warnings.some((w) => w.rule === "weak-joint"));
});
