// Explaining with bricks: four kinds of LEGO chart, each built from real data
// and checked as a buildable model, with the blueprint layer pinned on top.
//   bars      time to first token, four routing policies (Systems in Miniature)
//   heat      GPT-2's causal trace, words × layers (Model Microscope)
//   columns   the chance of "Paris", layer by layer (Model Microscope)
//   blocks    a prompt routed to the GPU that already has it cached
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { barChart, heatGrid, columns, blocks, LEGO, RAMPS } from "../lib/brickcharts.mjs";

const read = (rel) => fs.readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
// the cache-router miniature's default run, as baked for its page
const baked = read("../../../../systems/miniatures/site/baked/cache-router.js");
const runs = JSON.parse(baked.slice(baked.indexOf("{"), baked.lastIndexOf("}") + 1));
const router = Object.values(runs).find((r) => r.params.policy === "bounded") || Object.values(runs)[0];
const policies = router.stats;
const d = JSON.parse(read("../../../../ai/model-microscope/site/data/eiffel.json"));
const T = d.tokens.length, L = d.layers, target = d.targetToken.trim();
const lo = d.trace.pCorrupt, hi = d.clean, norm = (v) => Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
const ms = (s) => (s >= 1 ? `${s.toFixed(2)} s` : `${Math.round(s * 1000)} ms`);

export default explainer({ title: "Explaining with Bricks", description: "Four kinds of LEGO chart built from real data, each a checked, buildable model, with blueprint labels pinned on top.", music: true }, (s) => {
  // ---- 1 · bars
  const pColors = [LEGO.red, LEGO.orange, LEGO.mediumBlue, LEGO.brightGreen];
  const bars = barChart(policies.map((p) => p.ttftP50), { colors: pColors, maxPlates: 30, gap: 3 });
  s.together((g) => {
    g.heading("bars: four ways to route a prompt");
    g.dial(1, "bars", { of: 4 });
    g.bricks("bars", bars, { az: -28, el: 22, dist: 46, dur: 3200 });
    g.sfx("clicks", { dur: 3200 });
    g.narrate("Each bar is a stack of real LEGO bricks: the median wait for the first word, under four routing policies.", { dur: 4200 });
  });
  s.together((g) => {
    policies.forEach((p, i) => {
      g.text(`bv${i}`, ms(p.ttftP50), { anchor: { obj: "bars", at: `bar${i}`, dy: -34 }, size: 26, font: "mono", weight: 600, color: i === 3 ? "accent" : "ink", dur: 500 });
      g.text(`bl${i}`, p.label, { anchor: { obj: "bars", at: `foot${i}`, dy: 28 }, size: 18, color: "dim", dur: 500 });
    });
    g.sfx("type", { n: 8 });
    g.set("bars", { az: 18 }, { dur: 6500 });
    g.narrate(`Sending each prompt to the GPU that already read it cuts the wait from ${ms(policies[0].ttftP50)} to ${ms(policies[3].ttftP50)}.`, { dur: 4400 });
  });
  s.together((g) => g.clear(["bars", ...policies.flatMap((_, i) => [`bv${i}`, `bl${i}`])]));

  // ---- 2 · heat
  const heat = heatGrid(d.trace.mlp.map((r) => r.map(norm)), { ramp: RAMPS.green, maxPlates: 7 });
  s.together((g) => {
    g.heading("heat: where GPT-2 keeps a fact");
    g.dial(2, "heat map");
    g.bricks("heat", heat, { az: -20, el: 42, dist: 40, dur: 5200 });
    g.sfx("clicks", { dur: 5200 });
    g.narrate(`Every column is one word at one layer: how much putting back that MLP restores “${target}”. Taller and brighter means more.`, { dur: 5200 });
  });
  const key = d.trace.corrupt.reduce((b, r) => (Math.max(...d.trace.mlp[r]) > Math.max(...d.trace.mlp[b]) ? r : b), d.trace.corrupt[0]);
  const peak = d.trace.mlp[key].indexOf(Math.max(...d.trace.mlp[key]));
  s.together((g) => {
    d.tokens.forEach((w, r) => g.text(`hr${r}`, w.trim(), { anchor: { obj: "heat", at: `row${r}`, dx: -30 }, size: 16, font: "mono", align: "right", color: r === key ? "accent" : "dim", dur: 300 }));
    g.note("hn", `“${d.tokens[key].trim()}”, layer ${peak + 1}: the fact`, { anchor: { obj: "heat", at: `cell:${key}:${peak}`, ox: 150, oy: -150 }, color: "accent", dur: 900 });
    g.set("heat", { az: 22, el: 34 }, { dur: 7000 });
    g.narrate(`The ridge sits on one word: “${d.tokens[key].trim()}”, the end of “Eiffel”, in the middle layers.`, { dur: 4600 });
  });
  s.together((g) => g.clear(["heat", "hn", ...d.tokens.map((_, r) => `hr${r}`)]));

  // ---- 3 · columns, with a line through the tops
  const track = d.targetTrack.map((x) => x.p);
  const firstTop = d.targetTrack.findIndex((x) => x.rank === 1);
  const cols = columns(track, { log: true, min: 1e-5, gap: 0, maxPlates: 27, colors: track.map((_, l) => (l >= firstTop ? LEGO.orange : LEGO.mediumBlue)), cap: track.map((_, l) => (l >= firstTop ? LEGO.yellow : LEGO.white)) });
  s.together((g) => {
    g.heading("columns: the answer, layer by layer");
    g.dial(3, "columns");
    g.bricks("cols", cols, { az: -10, el: 16, dist: 44, dur: 4200 });
    g.sfx("clicks", { dur: 4200 });
    g.narrate(`One column per layer: the chance the model would say “${target}” if it stopped there, on a log scale.`, { dur: 4400 });
  });
  s.together((g) => {
    g.path("line", [], { anchors: track.map((_, l) => ({ obj: "cols", at: `top${l}` })), curve: false, color: "cyan", width: 2.5, arrow: false, dur: 2400 });
    g.sfx("sweep", { dur: 2400 });
    g.text("c0", "embed", { anchor: { obj: "cols", at: "foot0", dy: 26 }, size: 16, font: "mono", color: "dim" });
    g.text("c1", `layer ${firstTop}: ${target}`, { anchor: { obj: "cols", at: `top${firstTop}`, dy: -40 }, size: 22, font: "mono", weight: 600, color: "accent" });
    g.text("c2", `layer ${L}`, { anchor: { obj: "cols", at: `foot${L}`, dy: 26 }, size: 16, font: "mono", color: "dim" });
    g.set("cols", { az: 14 }, { dur: 6000 });
    g.narrate(`Almost nothing for sixteen layers, then a jump: from layer ${firstTop}, “${target}” is the top guess.`, { dur: 4400 });
  });
  s.together((g) => g.clear(["cols", "line", "c0", "c1", "c2"]));

  // ---- 4 · a block diagram
  // GPU 1 at the back, so the column reads 1 → 4 from the top of the frame
  const gpus = [0, 1, 2, 3].map((i) => ({ id: `gpu${i}`, x: 22, z: 1 + (3 - i) * 4, w: 4, d: 2, h: 2, color: LEGO.darkGray, cap: i === 2 ? LEGO.brightGreen : LEGO.lightGray }));
  const diagram = blocks([
    { id: "prompt", x: 2, z: 7, w: 2, d: 2, h: 1, color: LEGO.orange, cap: LEGO.yellow },
    { id: "router", x: 11, z: 6, w: 4, d: 2, h: 2, color: LEGO.mediumBlue, cap: LEGO.white },
    ...gpus,
  ], { width: 30, depth: 18 });
  s.together((g) => {
    g.heading("diagrams: where a prompt goes");
    g.dial(4, "diagrams");
    g.bricks("diag", diagram, { az: 0, el: 48, dist: 46, dur: 2600 });
    g.sfx("clicks", { dur: 2600 });
  });
  s.together((g) => {
    g.text("t0", "prompt", { anchor: { obj: "diag", at: "prompt", dy: -34 }, size: 20, font: "mono" });
    g.text("t1", "router", { anchor: { obj: "diag", at: "router", dy: -34 }, size: 20, font: "mono" });
    gpus.forEach((n, i) => g.text(`tg${i}`, `GPU ${i + 1}${i === 2 ? " · has it cached" : ""}`, { anchor: { obj: "diag", at: n.id, dx: 0, dy: -34 }, size: 18, font: "mono", color: i === 2 ? "green" : "dim" }));
    g.path("a1", [], { anchors: [{ obj: "diag", at: "prompt" }, { obj: "diag", at: "router" }], color: "accent", width: 3, pulses: 2, period: 1400, dur: 900 });
    g.narrate("Blocks and arrows: the router sends the prompt to the GPU that already has it cached.", { dur: 3800 });
  });
  s.together((g) => {
    g.path("a2", [], { anchors: [{ obj: "diag", at: "router" }, { obj: "diag", at: "gpu2" }], color: "green", width: 3, pulses: 3, period: 1400, dur: 900 });
    g.sfx("chime");
    g.set("diag", { az: 24, el: 38 }, { dur: 5000 });
    g.narrate("Every chart here is a real model: it passes the same checks as any brick-stage build, so you could build it on a table.", { dur: 5000 });
  });
  s.together((g) => g.clear(["diag", "t0", "t1", "a1", "a2", "dial", ...gpus.map((_, i) => `tg${i}`)]));
  s.together((g) => {
    g.heading("data");
    g.text("s1", "Routing: Systems in Miniature, cache-router (Go simulation, default run)", { x: 96, y: 300, size: 24, align: "left" });
    g.text("s2", `GPT-2: Model Microscope, ${d.model}, causal tracing after Meng et al. (2022) and the logit lens`, { x: 96, y: 350, size: 24, align: "left" });
    g.text("s3", "Every chart checked by brick-check: real parts, studs connected, one piece", { x: 96, y: 400, size: 24, align: "left", color: "dim" });
  });
  s.wait(3000);
});
