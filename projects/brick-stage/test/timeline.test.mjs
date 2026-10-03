import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { story, model, P } from "../lib/director.mjs";
const TL = createRequire(import.meta.url)("../lib/timeline.cjs");

const block = (name) => model(name, [P("3003", 15, 0, 0, 0), P("3003", 15, 0, 3, 0)]);

test("an actor walks from one place to the next and stays there", () => {
  const s = story({ title: "t" }, (d) => { d.build(block("a"), { at: [0, 0, 0], stagger: 0, dur: 100 }); d.move("a", [10, 0, 0], { dur: 1000, hop: 0 }); });
  assert.equal(TL.actorPos(s.actors.a, 50).x, 0);
  assert.equal(TL.actorPos(s.actors.a, 600).x, 5);         // halfway, by the symmetric ease
  assert.equal(TL.actorPos(s.actors.a, 5000).x, 10);
});

test("turns add up, and a figure faces the way it walks", () => {
  const s = story({ title: "t" }, (d) => {
    d.figure("f", [0, 0, 0], { dur: 100 });
    d.move("f", [10, 0, 0], { dur: 1000 });                 // walking toward +x
    d.turn("f", 90, { dur: 100 });
  });
  const pose = TL.figurePose(s.actors.f, 1050);
  assert.ok(Math.abs(pose.heading - Math.PI / 2) < 1e-6, `heading ${pose.heading}`);
  assert.ok(Math.abs(TL.figurePose(s.actors.f, 9999).heading - Math.PI) < 1e-6);
});

test("props ease between on and off", () => {
  const s = story({ title: "t" }, (d) => { d.room({ dur: 10 }); d.button("b", [0, 0, 0], { dur: 10 }); d.press("b", { dur: 100 }); d.wait(500); d.release("b", { dur: 100 }); });
  const b = s.props.b;
  assert.equal(TL.propLevel(b, 0), 0);
  assert.equal(TL.propLevel(b, 200), 1);
  assert.equal(TL.propLevel(b, 9999), 0);
});

test("the camera eases between shots and can follow an actor", () => {
  const s = story({ title: "t" }, (d) => {
    d.shot({ at: [0, 0, 0], az: 0, el: 10, dist: 20 }, 0);
    d.build(block("a"), { at: [0, 0, 0], stagger: 0, dur: 100 });
    d.shot({ at: [0, 0, 0], az: 90, el: 10, dist: 20 }, 1000);
    d.wait(1000);
    d.follow("a", { dur: 10, offset: [0, 0, 0] });
    d.move("a", [20, 0, 0], { dur: 1000, hop: 0 });
  });
  assert.equal(TL.cameraState(s, 0).az, 0);
  assert.equal(TL.cameraState(s, 600).az, 45);
  const end = TL.cameraState(s, 9999);
  assert.equal(end.x, 21);                                  // the actor's centre, 1 stud into its 2x2 footprint
});

test("chapters come from captions, sounds are in time order", () => {
  const s = story({ title: "t" }, (d) => { d.caption("one", "A"); d.build(block("a")); d.caption("two"); d.wait(100); d.clearCaption(); });
  assert.deepEqual(TL.chapters(s).map((c) => c.label), ["A · one", "two"]);
  const ev = TL.soundEvents(s);
  assert.equal(ev.filter((e) => e.kind === "click").length, 2);
  assert.ok(ev.every((e, i) => i === 0 || ev[i - 1].t <= e.t));
});

test("the stage check catches two actors walking into each other", () => {
  const s = story({ title: "t" }, (d) => {
    d.build(block("a"), { at: [0, 0, 0], stagger: 0, dur: 100 });
    d.build(block("b"), { at: [10, 0, 0], stagger: 0, dur: 100 });
    d.move("b", [1, 0, 0], { dur: 1000, hop: 0 });
  });
  const hits = TL.stageCollisions(s);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].pair, "a & b");
});

test("…and stays quiet when they keep their distance", () => {
  const s = story({ title: "t" }, (d) => {
    d.build(block("a"), { at: [0, 0, 0], stagger: 0, dur: 100 });
    d.build(block("b"), { at: [10, 0, 0], stagger: 0, dur: 100 });
    d.move("b", [3, 0, 0], { dur: 1000, hop: 0 });
    d.turn("b", 45);
  });
  assert.deepEqual(TL.stageCollisions(s), []);
});

test("a highlight glows during its window only", () => {
  const s = story({ title: "t" }, (d) => { d.build(block("a"), { stagger: 0, dur: 100 }); d.highlight("a", { dur: 1000 }); d.wait(2000); });
  const a = s.actors.a;
  assert.equal(TL.glow(a, 50), 0);
  assert.ok(TL.glow(a, 600) > 0.3);
  assert.equal(TL.glow(a, 1500), 0);
});
