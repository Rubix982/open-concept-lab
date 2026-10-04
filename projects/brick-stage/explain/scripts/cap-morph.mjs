// Capability: morph. Four bars of real bricks answer three questions about
// the same four routing policies; between questions the bricks fly from bar
// to bar. Data: Systems in Miniature's cache-router default run.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { barChart, columns, LEGO } from "../lib/brickcharts.mjs";

const read = (rel) => fs.readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
const baked = read("../../../../systems/miniatures/site/baked/cache-router.js");
const runs = JSON.parse(baked.slice(baked.indexOf("{"), baked.lastIndexOf("}") + 1));
const stats = (Object.values(runs).find((r) => r.params.policy === "bounded") || Object.values(runs)[0]).stats;

const colors = [LEGO.red, LEGO.orange, LEGO.mediumBlue, LEGO.brightGreen];
const ms = (s) => (s >= 1 ? `${s.toFixed(2)} s` : `${Math.round(s * 1000)} ms`);
const pct = (x) => `${Math.round(x * 100)}%`;
// same layout every time (gap, colours, base), so the bars line up and bricks can move between them
const chart = (vals, maxValue) => barChart(vals, { colors, gap: 3, maxPlates: 30, maxValue });
const Q = [
  { key: "ttftP50", title: "median wait for the first word", fmt: ms, max: Math.max(...stats.map((x) => x.ttftP50)) },
  { key: "hitRate", title: "prompts found in the cache", fmt: pct, max: 1 },
  { key: "maxBusy", title: "how busy the busiest GPU is", fmt: pct, max: 1 },
];
const models = Q.map((q) => chart(stats.map((x) => x[q.key]), q.max));

export default explainer({ title: "Morph: one model, three questions", description: "Real LEGO bars rebuild themselves from one question to the next.", music: true }, (s) => {
  s.together((g) => {
    g.heading(`morph · ${Q[0].title}`);
    g.morph("bars", null, null, { models, az: -26, el: 22, dist: 46, dur: 3000 });
    g.sfx("clicks", { dur: 3000 });
    g.narrate("Four routing policies, one bar each, built from real bricks.", { dur: 3000 });
  });
  const labels = (qi) => stats.map((x, i) => `v${qi}_${i}`);
  const showValues = (g, qi) => stats.forEach((x, i) => g.text(`v${qi}_${i}`, Q[qi].fmt(x[Q[qi].key]), { anchor: { obj: "bars", at: `m${qi}:bar${i}`, dy: -34 }, size: 26, font: "mono", weight: 600, color: i === 3 ? "accent" : "ink", dur: 500 }));
  s.together((g) => {
    showValues(g, 0);
    stats.forEach((x, i) => g.text(`name${i}`, x.label, { anchor: { obj: "bars", at: `foot${i}`, dy: 28 }, size: 18, color: "dim", dur: 500 }));
    g.sfx("type", { n: 8 });
    g.narrate(`Round robin waits ${ms(stats[0].ttftP50)}; the load-capped cache router ${ms(stats[3].ttftP50)}.`, { dur: 3600 });
  });

  for (let qi = 1; qi < Q.length; qi++) {
    s.together((g) => {
      g.clear(labels(qi - 1), { dur: 300 });
      g.heading(`morph · ${Q[qi].title}`);
    });
    s.together((g) => {
      g.set("bars", { morph: qi, az: -26 + qi * 18 }, { dur: 4200 });
      g.sfx("morph", { dur: 4200 });
      g.narrate(qi === 1 ? "Same bricks, a new question: how often was the prompt already cached?" : "And again: how hard is the busiest GPU working?", { dur: 4200 });
    });
    s.together((g) => {
      showValues(g, qi);
      g.sfx("type", { n: 8 });
      g.narrate(qi === 1
        ? `Round robin finds it ${pct(stats[0].hitRate)} of the time; routing by prompt, ${pct(stats[3].hitRate)}.`
        : `Plain affinity piles work on one GPU (${pct(stats[2].maxBusy)}); the load cap spreads it (${pct(stats[3].maxBusy)}).`, { dur: 3800 });
    });
  }
  // across kinds: the bars rebuild as round columns, one per GPU — bricks that
  // aren't the same part change shape mid-flight ("transmute")
  const busy = stats[3].busy;
  const perGpu = columns(busy, { maxValue: 1, maxPlates: 24, gap: 1, colors: busy.map(() => LEGO.brightGreen), cap: busy.map(() => LEGO.white) });
  s.together((g) => {
    g.clear(["bars", ...labels(Q.length - 1), ...stats.map((_, i) => `name${i}`)], { dur: 400 });
    g.heading("morph · across kinds of chart");
  });
  s.morph("split", null, null, { models: [models[Q.length - 1], perGpu], az: -10, el: 20, dist: "auto", dur: 600 });
  s.together((g) => {
    g.set("split", { morph: 1, az: 20 }, { dur: 4600 });
    g.sfx("morph", { dur: 4600 });
    g.narrate("Across kinds of chart, bricks change shape in flight: four bars become one column per GPU.", { dur: 4600 });
  });
  s.together((g) => {
    busy.forEach((b, i) => g.text(`gpu${i}`, `${Math.round(b * 100)}%`, { anchor: { obj: "split", at: `b:top${i}`, dy: -26 }, size: 18, font: "mono", dur: 400 }));
    g.narrate("With the load cap, every GPU carries a similar share.", { dur: 3000 });
  });
  s.wait(1500);
});
