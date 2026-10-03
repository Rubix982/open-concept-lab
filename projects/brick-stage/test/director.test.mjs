import test from "node:test";
import assert from "node:assert/strict";
import { story, model, P } from "../lib/director.mjs";

const tower = model("tower", [P("3003", 15, 0, 0, 0), P("3003", 15, 0, 3, 0)]);
const floating = model("floating", [P("3003", 15, 0, 0, 0), P("3003", 15, 0, 9, 0)]);

test("actions run one after another", () => {
  const s = story({ title: "t" }, (d) => { d.card("A", "a", { dur: 1000 }); d.build(tower, { stagger: 100, dur: 500 }); d.wait(250); });
  assert.equal(s.actors.tower.parts[0].t0, 1000);
  assert.equal(s.actors.tower.parts[1].t0, 1100);
  assert.equal(s.duration, 1000 + 100 + 500 + 250 + 600);
});

test("together() starts everything at once and waits for the longest", () => {
  const s = story({ title: "t" }, (d) => {
    d.build(tower, { stagger: 100, dur: 500 });
    d.together((g) => { g.move("tower", [5, 0, 0], { dur: 2000 }); g.wait(300); });
    d.wait(0);
  });
  assert.equal(s.actors.tower.moves[1].t, 600);
  assert.equal(s.duration, 600 + 2000 + 600);
});

test("a model that can't be built is reported", () => {
  const s = story({ title: "t" }, (d) => d.build(floating));
  assert.equal(s.reports.floating.ok, false);
});

test("build onto checks the combined model", () => {
  const top = model("top", [P("3003", 15, 0, 6, 0)]);
  const s = story({ title: "t" }, (d) => { d.build(tower); d.build(top, { onto: "tower" }); });
  assert.deepEqual(Object.keys(s.reports), ["tower + top"]);
  assert.equal(s.reports["tower + top"].ok, true);
  assert.equal(s.actors.tower.parts.length, 3);
});
