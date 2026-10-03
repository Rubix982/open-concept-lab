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

test("joints ease to absolute angles and back", () => {
  const arm = model("arm-bot", [P("3003", 15, 0, 0, 0), P("3005", 15, 2, 0, 0)], { joints: { arm: { parts: [1], pivot: [2.5, 3, 0.5], axis: "x" } } });
  const s = story({ title: "t" }, (d) => { d.build(arm, { stagger: 0, dur: 100 }); d.pose("arm-bot", "arm", 90, { dur: 400 }); d.pose("arm-bot", "arm", 0, { dur: 400 }); });
  const a = s.actors["arm-bot"];
  assert.equal(TL.jointAngle(a, "arm", 0), 0);
  assert.equal(TL.jointAngle(a, "arm", 500), 90);
  assert.equal(TL.jointAngle(a, "arm", 9999), 0);
});

test("a joint naming a missing part is refused", () => {
  assert.throws(() => model("x", [P("3003", 15, 0, 0, 0)], { joints: { arm: { parts: [4], pivot: [0, 0, 0] } } }), /doesn't exist/);
});

test("moods blend, letterbox and fades ease in and out", () => {
  const s = story({ title: "t" }, (d) => {
    d.mood("sunset", { dur: 1000 }); d.letterbox(true, { dur: 500 }); d.wait(2000);
    d.mood("night", { dur: 1000 }); d.fadeOut({ dur: 500 }); d.fadeIn({ dur: 500 });
  });
  const w = TL.moodWeights(s, 500);
  assert.ok(Math.abs(w.day - 0.5) < 1e-9 && Math.abs(w.sunset - 0.5) < 1e-9);
  assert.equal(TL.moodWeights(s, 99999).night, 1);
  assert.equal(TL.level(s.letterboxes, 9999), 1);
  assert.equal(TL.level(s.fades, 2500), 1);
  assert.equal(TL.level(s.fades, 9999), 0);
});

test("music plays one chord a bar until it stops", () => {
  const s = story({ title: "t" }, (d) => { d.music("romance"); d.wait(5000); d.music(null); d.wait(5000); });
  const chords = TL.soundEvents(s).filter((e) => e.kind === "chord");
  assert.deepEqual(chords.map((c) => c.t), [0, 2400, 4800]);
});

test("an attached sub-assembly lands where asked, then rides along with its host", () => {
  const base = model("base", [P("3020", 15, 0, 0, 0)]);           // 2x4 plate
  const top = model("top", [P("3003", 4, 0, 0, 0)]);              // 2x2 brick
  const s = story({ title: "t" }, (d) => {
    d.build(base, { at: [0, 0, 0], stagger: 0, dur: 100 });
    d.build(top, { at: [10, 0, 5], stagger: 0, dur: 100 });
    d.attach("top", { onto: "base", at: [1, 1, 0], dur: 1000 });
    d.move("base", [20, 0, 0], { dur: 1000, hop: 0 });
  });
  // checked twice: the sub-assembly on its own (it's built on the table first), then the whole
  assert.deepEqual(Object.keys(s.reports).sort(), ["base + top", "top (built on its own)"]);
  assert.equal(s.reports["base + top"].ok, true);
  assert.equal(s.reports["top (built on its own)"].ok, true);
  const landed = TL.actorPos(s.actors.top, 1200, s.actors);   // the attach runs 200–1200 ms
  const midway = TL.actorPos(s.actors.top, 700, s.actors);
  assert.ok(midway.y >= 2, "it travels above the host, not through it");
  assert.deepEqual([landed.x, landed.y, landed.z].map((v) => Math.round(v * 1000) / 1000), [1, 1, 0]);
  const after = TL.actorPos(s.actors.top, 9999, s.actors);
  assert.deepEqual([after.x, after.y, after.z].map((v) => Math.round(v * 1000) / 1000), [21, 1, 0]);
});

test("parts can fly in along their real insertion path", () => {
  const roofed = model("roofed", [
    P("3020", 15, 0, 0, 0), P("3003", 15, 0, 1, 0), P("3022", 15, 0, 4, 0), P("3020", 15, 0, 5, 0), P("3003", 4, 2, 1, 0),
  ]);
  const s = story({ title: "t" }, (d) => d.build(roofed, { from: "path" }));
  const parts = s.actors.roofed.parts;
  assert.equal(parts[0].via, "down");
  assert.equal(parts[4].via, "slide+x");
  assert.ok(parts[4].from[0] > 0 && Math.abs(parts[4].from[1]) < 2, "slides in from +x");
});

test("narration waits long enough to be read, or not at all when asked", () => {
  const s = story({ title: "t" }, (d) => {
    d.narrate("Five words to read aloud.");                 // 5 words ≈ 600 + 1923 ms
    d.narrate("Under the next action.", { wait: false, dur: 3000 });
    d.wait(1000);
  });
  assert.equal(s.narration.length, 2);
  assert.equal(s.narration[0].dur, 2523);
  assert.equal(s.narration[1].t, 2523);
  assert.equal(s.duration, 2523 + 1000 + 600);
});

test("turnTo faces a heading, the camera, or another actor, the short way round", () => {
  const s = story({ title: "t" }, (d) => {
    d.shot({ at: [0, 0, 0], az: 30, el: 10, dist: 20 }, 0);
    d.minifig("a", [0, 0, 0], { dur: 10 });
    d.minifig("b", [10, 0, 0], { dur: 10 });
    d.turnTo("a", "b", { dur: 10 });          // b is to stage right: +90
    d.turnTo("a", "camera", { dur: 10 });     // back to 30
    d.turnTo("a", -170, { dur: 10 });         // the short way: -200, not +160
  });
  const turns = s.actors.a.turns.map((k) => Math.round(k.deg));
  assert.deepEqual(turns, [90, -60, 160]);
  assert.equal(Math.round((TL.figurePose(s.actors.a, 9999).heading * 180) / Math.PI), 190);
});

test("the stage check follows joints: a swung-away arm no longer collides", () => {
  const gate = model("gate", [P("3003", 15, 0, 0, 0), P("3009", 4, 2, 0, 0)],          // a post, and a 1x6 arm along x
    { joints: { arm: { parts: [1], pivot: [2, 3, 0.5], axis: "y" } } });
  const s = story({ title: "t" }, (d) => {
    d.build(gate, { at: [0, 0, 0], stagger: 0, dur: 100 });
    d.build(model("box", [P("3003", 15, 0, 0, 0)]), { as: "box", at: [1, 0, 5], stagger: 0, dur: 100 });   // where the arm swings to
    d.pose("gate", "arm", 90, { dur: 500 });                                          // swings the arm toward the box
    d.wait(200);
    d.pose("gate", "arm", 0, { dur: 500 });
  });
  const hits = TL.stageCollisions(s);
  assert.equal(hits.length, 1, "the arm reaches the box only when swung");
  assert.ok(hits[0].t > 200, `caught while swung, not at rest (t=${hits[0].t})`);
});
