// Microduck, in Bricks — the brick-stage take on the Microduck booklet.
// The shape is sampled from Pollen Robotics' open Microduck CAD (Apache-2.0)
// by brick-check's brickify tool (run tools/microduck-model.mjs first), then
// built the way the booklet builds it: in sections, with the head made as a
// sub-assembly and set on the neck. Every part arrives along the path
// brick-check says it really goes in.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { story, model } from "../lib/director.mjs";

const file = fileURLToPath(new URL("../../brick-check/out/microduck/microduck-bricks.json", import.meta.url));
const { parts } = JSON.parse(fs.readFileSync(file, "utf8"));

// Split by build order where everything after is at or above a given layer,
// so each section sits on the one before it.
const suffixMin = []; for (let i = parts.length - 1, m = Infinity; i >= 0; i--) suffixMin[i] = m = Math.min(m, parts[i].y);
const splitAt = (y) => suffixMin.findIndex((v) => v >= y);
const legsEnd = splitAt(28), headStart = splitAt(52);
const legs = model("legs", parts.slice(0, legsEnd));
const trunk = model("trunk and neck", parts.slice(legsEnd, headStart));
const head = model("head", parts.slice(headStart).map((p) => ({ ...p, y: p.y - 52 })));

export default story({
  title: "Microduck, in Bricks", poster: 27000, drift: 0.4,
  subtitle: "the small open-source biped robot by Pollen Robotics, sampled from its CAD into LEGO plates",
  about: "A brick model of Microduck, the open-source biped robot by Pollen Robotics, in its standing pose. Its shape was sampled from the robot's own CAD model into a grid of LEGO plates by brick-check's brickify tool. An unofficial fan model, not produced or endorsed by Pollen Robotics.",
  sources: ["Robot: Pollen Robotics Microduck, CAD from github.com/pollen-robotics/microduck_rl (Apache-2.0)", "Idea: the Microduck LEGO booklet (huggingface.co/buckets/victor/microduck-lego-booklet)"],
}, (s) => {
  s.shot({ at: [7, 30, 6], az: 30, el: 18, dist: 56 }, 0);
  s.card("A BRICK MODEL OF", "Microduck", { sub: "sampled from Pollen Robotics' open CAD into 670 LEGO plates", dur: 3400 });

  s.section("Feet and legs");
  s.shot({ at: [7, 12, 6], az: 24, el: 22, dist: 40 }, 2500);
  s.build(legs, { at: [0, 0, 0], from: "path", stagger: 20, dur: 550 });

  s.section("Trunk and neck");
  s.shot({ at: [7, 30, 6], az: 12, el: 16, dist: 48 }, 2500);
  s.build(trunk, { onto: "legs", from: "path", stagger: 22, dur: 550 });

  s.section("Head, as a sub-assembly");
  s.shot({ at: [24, 6, 6], az: -10, el: 26, dist: 36 }, 2000);
  s.build(head, { as: "head", at: [20, 0, 0], from: "path", stagger: 24, dur: 550 });
  s.callout("Built on its own, then set on the neck", { on: "head", dur: 2400 });
  s.wait(800);
  s.together((g) => {
    g.shot({ at: [10, 40, 6], az: 4, el: 12, dist: 74 }, 2200);
    g.attach("head", { onto: "legs", at: [0, 52, 0], dur: 2200, lift: 14 });
  });

  s.caption("670 plates. Checked on a computer, not yet with real bricks.");
  s.wait(2600);
  s.clearCaption();
  s.turnaround("legs", { dur: 7000, el: 10, dist: 66, offset: [0, 32, 0] });
  s.wait(7000);
  s.card("SHAPE FROM", "Pollen Robotics' Microduck", { sub: "open CAD, Apache-2.0 · an unofficial fan model", dur: 3200 });
});
