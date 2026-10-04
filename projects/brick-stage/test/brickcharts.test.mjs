// Every brick chart, across data shapes, must be a real model: brick-check
// passes (vocabulary, no collisions, studs connect, one piece) and the
// anchors the 2D layer pins to are there.
import test from "node:test";
import assert from "node:assert/strict";
import { check } from "../../brick-check/lib/check.mjs";
import * as B from "../explain/lib/brickcharts.mjs";

function ok(name, chart, wantAnchors = []) {
  const r = check({ steps: [{ note: name, parts: chart.parts }] });
  assert.ok(r.ok, `${name}: ${[...new Set(r.errors.map((e) => `${e.rule}: ${e.msg}`))].slice(0, 3).join(" | ")}`);
  for (const a of wantAnchors) {
    assert.ok(chart.anchors[a], `${name}: missing anchor ${a}`);
    assert.ok(chart.anchors[a].every(Number.isFinite), `${name}: anchor ${a} is not a point`);
  }
  assert.equal(chart.size.length, 3);
}
const rnd = (seed) => () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

test("base is one piece at every size", () => {
  for (let w = 2; w <= 30; w++) for (let d = 2; d <= 20; d++) ok(`base ${w}×${d}`, { parts: B.base(w, d), anchors: {}, size: [w, 2, d] });
});

test("the original four still build", () => {
  ok("bars", B.barChart([580, 281, 29, 28]), ["bar0", "foot3"]);
  ok("heat", B.heatGrid([[0, 0.5, 1], [1, 0.2, 0]]), ["cell:1:2", "row0", "col2"]);
  ok("columns", B.columns([1e-4, 0.01, 0.9], { log: true }), ["top2", "foot0"]);
  ok("blocks", B.blocks([{ id: "a", x: 1, z: 1, w: 2, d: 2 }, { id: "b", x: 6, z: 3, w: 4, d: 2, h: 3, cap: 15 }]), ["a", "b.front"]);
});

test("stackedBars", () => {
  ok("one bar, one segment", B.stackedBars([[1]]), ["bar0", "seg0:0", "foot0"]);
  ok("with zeros and an empty bar", B.stackedBars([[3, 0, 2], [0, 0, 0], [1, 1, 1]]), ["bar1", "seg2:2"]);
  const r = rnd(3), many = Array.from({ length: 9 }, () => Array.from({ length: 4 }, () => r() * 10));
  ok("nine bars of four", B.stackedBars(many), ["bar8", "seg8:3"]);
});

test("groupedBars", () => {
  ok("one group", B.groupedBars([[2, 5]]), ["bar0:1", "group0"]);
  ok("uneven groups", B.groupedBars([[1, 2, 3], [4], [0, 2]]), ["bar1:0", "bar2:1", "group2"]);
});

test("numberLine", () => {
  ok("bare", B.numberLine(0, 1), ["tick0", "tick1", "start", "end"]);
  ok("ticks and stacked marks", B.numberLine(-5, 5, { length: 21, ticks: [-5, 0, 5], marks: [{ value: 0 }, { value: 0, color: 4 }, { value: 4.6, height: 2 }] }), ["mark0", "mark1", "mark2"]);
  ok("odd length", B.numberLine(1700, 1800, { length: 17, ticks: [1700, 1732, 1745, 1800] }), ["tick3"]);
});

test("scatter", () => {
  ok("single point at zero", B.scatter([[0, 0]]), ["pt0", "xmin", "xmax"]);
  const r = rnd(7), pts = Array.from({ length: 40 }, () => [r() * 10, r() * 5, Math.floor(r() * 3)]);
  ok("forty points with collisions", B.scatter(pts, { length: 15 }), ["pt39"]);
});

test("waffle", () => {
  for (const p of [0, 1, 37, 99, 100]) {
    const w = B.waffle(p);
    ok(`waffle ${p}%`, w);
    assert.equal(w.counts.reduce((a, v) => a + v, 0), 100);
  }
  ok("three categories", B.waffle([1, 1, 1]), ["cat0", "cat2", "cell99"]);
});

test("matrix", () => {
  ok("1×1", B.matrix([[0.5]]), ["cell:0:0", "row0", "col0"]);
  const r = rnd(11), m = Array.from({ length: 11 }, () => Array.from({ length: 11 }, () => r()));
  ok("11×11 raised", B.matrix(m, { raise: true }), ["cell:10:10", "row10", "col10"]);
  ok("ragged rows", B.matrix([[1, 0, 1], [0.2]]), ["cell:0:2"]);
});

test("graph and tree", () => {
  const nodes = [{ id: "a", x: 1, z: 1, w: 2, d: 2 }, { id: "b", x: 10, z: 1, w: 4, d: 2, h: 2 }, { id: "c", x: 10, z: 9, w: 2, d: 2 }, { id: "d", x: 1, z: 9, w: 2, d: 2 }];
  ok("square with a diagonal", B.graph(nodes, [{ from: "a", to: "b" }, { from: "b", to: "c" }, { from: "c", to: "d" }, { from: "a", to: "c" }]), ["edge0:mid", "edge3:turn", "a"]);
  ok("single node, no edges", B.graph([{ id: "x", x: 1, z: 1, w: 2, d: 2 }], []), ["x"]);
  assert.throws(() => B.graph(nodes, [{ from: "a", to: "zz" }]));
  ok("tree", B.tree({ id: "root", children: [{ id: "l", children: [{ id: "l1" }, { id: "l2" }, { id: "l3" }] }, { id: "r", children: [{ id: "r1" }] }] }), ["root", "l3", "edge0:mid"]);
});

test("axes", () => {
  const bars = B.barChart([5, 3, 8]);
  ok("axes by plates", B.axes(bars, { ticks: [6, 12, 18] }), ["ytick0", "ytick2", "bar0"]);
  ok("axes from a chart's own scale", B.axes(B.stackedBars([[2, 3], [5, 1]]), { ticks: [2, 4, 6] }), ["ytick2", "seg1:0"]);
});
