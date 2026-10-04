// Capability test: the minifig presenter. It walks in, waves, points at the
// slowest and the fastest bar of a brick chart while the captions play,
// shrugs, nods, thinks, and walks off. Data: the cache-router miniature's
// default run (Systems in Miniature).
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { barChart, LEGO } from "../lib/brickcharts.mjs";

const baked = fs.readFileSync(fileURLToPath(new URL("../../../../systems/miniatures/site/baked/cache-router.js", import.meta.url)), "utf8");
const runs = JSON.parse(baked.slice(baked.indexOf("{"), baked.lastIndexOf("}") + 1));
const run = Object.values(runs).find((r) => r.params.policy === "bounded") || Object.values(runs)[0];
const stats = run.stats;
const ms = (s) => (s >= 1 ? `${s.toFixed(2)} s` : `${Math.round(s * 1000)} ms`);
const slow = stats.reduce((a, b, i) => (b.ttftP50 > stats[a].ttftP50 ? i : a), 0);
const fast = stats.reduce((a, b, i) => (b.ttftP50 < stats[a].ttftP50 ? i : a), 0);

export default explainer({ title: "Meet the Presenter", description: "A LEGO minifig host walks in and presents a brick chart.", music: true }, (s) => {
  const bars = barChart(stats.map((p) => p.ttftP50), { colors: [LEGO.red, LEGO.orange, LEGO.mediumBlue, LEGO.brightGreen], maxPlates: 30, gap: 3 });
  s.together((g) => {
    g.heading("the presenter");
    g.bricks("bars", bars, { x: 520, y: 60, w: 1400, h: 1000, az: -22, el: 20, dist: 46, dur: 2600 });
    g.sfx("clicks", { dur: 2600 });
  });
  // created after the chart, so pointing sees this frame's chart camera
  s.presenter("host", { x: 40, y: 330, w: 560, h: 720, look: { torso: 1, legs: 72, print: "sweater", hat: "cap", hatColor: 4, face: "smile" } });
  s.together((g) => {
    stats.forEach((p, i) => {
      g.text(`v${i}`, ms(p.ttftP50), { anchor: { obj: "bars", at: `bar${i}`, dy: -34 }, size: 24, font: "mono", weight: 600, color: i === fast ? "accent" : "ink", dur: 400 });
      g.text(`l${i}`, p.label, { anchor: { obj: "bars", at: `foot${i}`, dy: 28 }, size: 17, color: "dim", dur: 400 });
    });
  });
  s.walkIn("host");
  s.together((g) => {
    g.present("host", "wave", { dur: 2600 });
    g.narrate("Hi! Let me walk you through this chart.", { dur: 2600 });
  });
  s.together((g) => {
    g.present("host", "point", { at: { obj: "bars", at: `bar${slow}` }, dur: 3400 });
    g.narrate(`${stats[slow].label}: ${ms(stats[slow].ttftP50)} before the first word appears.`, { dur: 3400 });
  });
  s.together((g) => {
    g.face("host", "grin");
    g.present("host", "point", { at: { obj: "bars", at: `bar${fast}` }, dur: 3400 });
    g.narrate(`${stats[fast].label}: ${ms(stats[fast].ttftP50)}.`, { dur: 3400 });
  });
  s.together((g) => {
    g.face("host", "surprised");
    g.present("host", "shrug", { dur: 2400 });
    g.narrate("Same GPUs, same traffic. Only the routing changed.", { dur: 2400 });
  });
  s.together((g) => {
    g.face("host", "smile");
    g.present("host", "nod", { dur: 1600 });
  });
  s.together((g) => {
    g.present("host", "think", { dur: 2200 });
    g.narrate("Where should the next prompt go? That's the next chart.", { dur: 2200 });
  });
  s.walkOut("host");
  s.wait(600);
});
