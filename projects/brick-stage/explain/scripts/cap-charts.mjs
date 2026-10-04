// Capability: the newer brick charts, one each, on real data from the repo.
//   stacked bars + axes   the double-charge miniature's outcomes per policy
//   grouped bars          cache-router: prompt cache hits vs busiest GPU
//   number line           GPT-2's guesses for "from 1732 to 17__"
//   scatter               GPU speed-up over CPU, Metal bench on an M2 Pro
//   waffle                with no idempotency key: charged once / twice
//   matrix                GPT-2 attention, one layer, the Eiffel prompt
//   graph                 how an explainer is made (this library)
//   tree                  Systems in Miniature, by group
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { stackedBars, groupedBars, numberLine, scatter, waffle, matrix, graph, tree, axes, LEGO, RAMPS } from "../lib/brickcharts.mjs";

const read = (rel) => fs.readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
const baked = (name) => { const s = read(`../../../../systems/miniatures/site/baked/${name}.js`); return Object.values(JSON.parse(s.slice(s.indexOf("{"), s.lastIndexOf("}") + 1)))[0]; };
const charge = baked("double-charge").stats, router = baked("cache-router").stats;
const years = JSON.parse(read("../../../../ai/model-microscope/site/data/years.json"));
const eiffel = JSON.parse(read("../../../../ai/model-microscope/site/data/eiffel.json"));
const bench = JSON.parse(read("../../../../hpc/metal-gpu-bench/results/bench-2026-10-04.json"));
const pct = (v) => `${Math.round(v * 100)}%`;
// a camera distance that fits a chart's footprint and height
const fit = (c, k = 1) => Math.round((Math.max(c.size[0], c.size[2] * 1.2, c.size[1] * 0.5) * 1.55 + 10) * k);

export default explainer({ title: "More Brick Charts", description: "Stacked and grouped bars, a number line, scatter, waffle, matrix, graph and tree, built from real data as checked LEGO models.", music: true }, (s) => {
  let n = 0;
  const chapter = (title, short, id, chart, cam, labels, said) => {
    n++;
    s.together((g) => {
      g.heading(title);
      g.dial(n, short, { of: 8 });
      g.bricks(id, chart, { dist: fit(chart), ...cam, dur: Math.min(3200, 600 + chart.parts.length * 10) });
      g.sfx("clicks", { dur: 2400 });
      g.narrate(said, { dur: 3600 });
    });
    const ids = [];
    s.together((g) => {
      labels(g, (lid) => { ids.push(lid); return lid; });
      g.set(id, { az: (cam.az ?? 25) + 30 }, { dur: 3400 });
      g.wait(2600);
    });
    s.together((g) => g.clear([id, ...ids]));
  };
  const label = (g, id, text, at, o = {}) => g.text(id, text, { anchor: { obj: o.obj, at, dx: o.dx || 0, dy: o.dy ?? -26 }, size: o.size ?? 18, font: "mono", weight: 600, color: o.color || "ink", align: o.align || "center", dur: 400 });

  // ---- stacked bars, with a y axis
  const outcomes = charge.map((p) => [p.once, p.twice, p.never]);
  const sb = axes(stackedBars(outcomes, { colors: [LEGO.brightGreen, LEGO.red, LEGO.darkTan], maxPlates: 27, gap: 4 }), { ticks: [100, 200, 300, 400, 500] });
  chapter("stacked bars: who got charged how often", "stacked", "sb", sb, { az: -25, el: 20 }, (g, id) => {
    charge.forEach((p, i) => {
      label(g, id(`sbl${i}`), p.label, `foot${i}`, { obj: "sb", dy: 26, size: 15, color: "dim" });
      if (p.twice) label(g, id(`sbt${i}`), `${p.twice} twice`, `seg${i}:1`, { obj: "sb", dx: 64, dy: 0, color: "accent", size: 16 });
    });
    [100, 300, 500].forEach((v, k) => label(g, id(`sby${k}`), String(v), `ytick${[0, 2, 4][k]}`, { obj: "sb", dx: -26, dy: 0, align: "right", size: 14, color: "dim" }));
  }, `${charge.length} ways to handle a retried payment, 500 purchases each: green once, red twice.`);

  // ---- grouped bars
  const gb = groupedBars(router.map((p) => [p.hitRate, p.maxBusy]), { colors: [LEGO.brightGreen, LEGO.orange], maxValue: 1, maxPlates: 27 });
  chapter("grouped bars: cache hits against the busiest GPU", "grouped", "gb", gb, { az: -20, el: 18 }, (g, id) => {
    router.forEach((p, i) => {
      label(g, id(`gbl${i}`), p.label, `group${i}`, { obj: "gb", dy: 26, size: 15, color: "dim" });
      label(g, id(`gbh${i}`), pct(p.hitRate), `bar${i}:0`, { obj: "gb", color: "green", size: 15 });
      label(g, id(`gbb${i}`), pct(p.maxBusy), `bar${i}:1`, { obj: "gb", color: "accent", size: 15 });
    });
  }, "Green: prompts found in cache. Orange: how busy the busiest GPU is. Same traffic, four routers.");

  // ---- number line
  const guesses = years.says.slice(0, 3).map(([t, p]) => ({ year: 1700 + Number(t), p }));
  const nl = numberLine(1720, 1760, { length: 41, ticks: [1720, 1732, 1740, 1750, 1760], marks: guesses.map((x, i) => ({ value: x.year, color: i ? LEGO.mediumBlue : LEGO.orange, height: i ? 1 : 2 })) });
  chapter("number line: “from 1732 to 17__”", "number line", "nl", nl, { az: -6, el: 30, dist: fit(nl, 0.62) }, (g, id) => {
    [1720, 1732, 1740, 1750, 1760].forEach((y, i) => label(g, id(`nlt${i}`), String(y), `tick${i}`, { obj: "nl", dy: 24, size: 15, color: y === 1732 ? "accent" : "dim" }));
    guesses.forEach((x, i) => label(g, id(`nlm${i}`), `${x.year} · ${(x.p * 100).toFixed(1)}%`, `mark${i}`, { obj: "nl", dy: -28 - i * 22, size: 15, color: i ? "cyan" : "accent" }));
  }, "GPT-2's top three guesses for the end year: all after 1732, but none of them sure.");

  // ---- scatter
  const nb = bench.nbody.map((r) => [Math.log2(r.n) - 8, r.cpuMs / r.gpuMs, 0]);
  const st = bench.stencil.map((r) => [Math.log2(r.size) - 8, r.cpuMs / r.gpuMs, 1]);
  const sc = scatter([...nb, ...st], { xMax: 8, length: 25, colors: [LEGO.orange, LEGO.mediumBlue], maxPlates: 20 });
  chapter("scatter: how much faster the GPU is", "scatter", "sc", sc, { az: -15, el: 16, dist: fit(sc, 0.8) }, (g, id) => {
    const big = nb.length - 1;
    label(g, id("scn"), `gravity, 65,536 bodies: ${nb[big][1].toFixed(0)}×`, `pt${big}`, { obj: "sc", color: "accent", size: 15 });
    label(g, id("scs"), `heat, 8192²: ${st[st.length - 1][1].toFixed(1)}×`, `pt${nb.length + st.length - 1}`, { obj: "sc", color: "cyan", size: 15 });
    label(g, id("scx0"), "small", "xmin", { obj: "sc", dy: 24, size: 14, color: "dim" });
    label(g, id("scx1"), "large", "xmax", { obj: "sc", dy: 24, size: 14, color: "dim" });
  }, "Each post is one size: orange is gravity, blue is heat. Height is the GPU's lead over 12 CPU cores.");

  // ---- waffle
  const nk = charge[0], wf = waffle([nk.once, nk.twice, nk.never], { colors: [LEGO.brightGreen, LEGO.red, LEGO.darkTan] });
  chapter("waffle: one tile per hundredth", "waffle", "wf", wf, { az: -10, el: 55 }, (g, id) => {
    label(g, id("wf0"), `${pct(nk.once / 500)} once`, "cat0", { obj: "wf", color: "green", dy: 0 });
    if (wf.anchors.cat1) label(g, id("wf1"), `${pct(nk.twice / 500)} twice`, "cat1", { obj: "wf", color: "accent", dy: 0 });
  }, `With no idempotency key, ${nk.twice} of 500 customers paid twice: ${wf.counts[1]} tiles in a hundred.`);

  // ---- matrix: attention at one layer, first word left out
  const layer = 17, toks = eiffel.tokens.slice(1).map((t) => t.trim());
  const att = eiffel.attention.mean[layer].slice(1).map((row) => { const r = row.slice(1); const m = Math.max(1e-9, ...r); return r.map((v) => v / m); });
  const mx = matrix(att, { ramp: RAMPS.violet, raise: true, maxPlates: 3 });
  chapter(`matrix: who looks at whom, layer ${layer + 1}`, "matrix", "mx", mx, { az: -15, el: 52 }, (g, id) => {
    toks.forEach((t, r) => label(g, id(`mxr${r}`), t, `row${r}`, { obj: "mx", dx: -10, dy: 0, align: "right", size: 13, color: "dim" }));
    const last = toks.length - 1, peak = att[last].indexOf(1);
    label(g, id("mxp"), `“${toks[last]}” → “${toks[peak]}”`, `cell:${last}:${peak}`, { obj: "mx", color: "accent", size: 16, dy: -30 });
  }, "Each row is a word, each column a word before it: how much it attends there, the first word left out.");

  // ---- graph: how an explainer is made
  const gr = graph([
    { id: "script", x: 1, z: 2, w: 2, d: 2, h: 1, color: LEGO.orange, cap: LEGO.yellow },
    { id: "plugins", x: 1, z: 10, w: 2, d: 2, h: 1, color: LEGO.mediumLavender },
    { id: "build", x: 9, z: 6, w: 4, d: 2, h: 2, color: LEGO.mediumBlue, cap: LEGO.white },
    { id: "page", x: 19, z: 2, w: 2, d: 2, h: 1, color: LEGO.brightGreen },
    { id: "mp4", x: 19, z: 10, w: 2, d: 2, h: 1, color: LEGO.red },
  ], [{ from: "script", to: "build" }, { from: "plugins", to: "build" }, { from: "build", to: "page" }, { from: "page", to: "mp4", color: LEGO.yellow }], { width: 24, depth: 14 });
  chapter("graph: how an explainer is made", "graph", "gr", gr, { az: 0, el: 50 }, (g, id) => {
    [["script", "script.mjs"], ["plugins", "plugins/*.js"], ["build", "build.mjs + brick-check"], ["page", "index.html"], ["mp4", "render.mjs → mp4"]].forEach(([k, t]) => label(g, id(`gr${k}`), t, k, { obj: "gr", dy: -30, size: 15 }));
  }, "Roads of tiles are the edges: a script and its plugins are built, checked, and rendered to video.");

  // ---- tree
  const tr = tree({ id: "all", h: 2, children: [
    { id: "serve", children: [{ id: "s1" }, { id: "s2" }, { id: "s3" }, { id: "s4" }] },
    { id: "back", children: [{ id: "b1" }, { id: "b2" }, { id: "b3" }] },
  ] }, { colors: [LEGO.orange, LEGO.mediumBlue, LEGO.lightGray], xGap: 2, zGap: 3 });
  chapter("tree: Systems in Miniature", "tree", "tr", tr, { az: 0, el: 55 }, (g, id) => {
    label(g, id("tra"), "Systems in Miniature", "all", { obj: "tr", dy: -30, size: 16, color: "accent" });
    label(g, id("trs"), "serving LLMs · 4", "serve", { obj: "tr", dy: -30, size: 15 });
    label(g, id("trb"), "everyday backend · 3", "back", { obj: "tr", dy: -30, size: 15 });
  }, "A tree is a graph laid out by depth: one series, two groups, seven simulations.");

  s.together((g) => { g.clear(["dial"]); g.heading("eight more ways to build a chart"); });
  s.wait(2500);
});
