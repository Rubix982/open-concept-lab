// Where GPT-2 keeps a fact — a blueprint explainer.
// Every number on screen is read from Model Microscope's results for the
// Eiffel Tower prompt (ai/model-microscope/site/data/eiffel.json), at build time.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";

const d = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../../../../ai/model-microscope/site/data/eiffel.json", import.meta.url)), "utf8"));
const T = d.tokens.length, L = d.layers, last = T - 1, target = d.targetToken.trim();
const pct = (p) => (p >= 0.1 ? `${Math.round(p * 100)}%` : `${(p * 100).toFixed(1)}%`);
const lo = d.trace.pCorrupt, hi = d.clean, norm = (v) => Math.max(0, Math.min(1, (v - lo) / (hi - lo)));

// lens 1: what the last word would predict at each layer, as runs of the same guess
const guess = d.lens.map((layer) => layer[last][0][0].trim());
const runs = [];
guess.forEach((g, l) => (runs.length && runs.at(-1).g === g ? (runs.at(-1).b = l) : runs.push({ g, a: l, b: l })));
const name = (l) => (l === 0 ? "embed" : `L${l}`);
const runText = (r) => `${r.a === r.b ? name(r.a) : `${name(r.a)}–${r.b}`}  ${r.g}`;
const firstTop = d.targetTrack.findIndex((x) => x.rank === 1);
const london = guess.map((g, l) => (g === "London" ? l : -1)).filter((l) => l >= 0);

// lens 3: causal traces, rows = words, columns = layers, scaled from scrambled to clean
const heat = (kind) => d.trace[kind].map((row) => row.map(norm));
const subj = d.trace.corrupt;
// the position whose MLPs bring the answer back most (for Eiffel: "el", not " Tower")
const subjLast = subj.reduce((best, r) => (Math.max(...d.trace.mlp[r].map(norm)) > Math.max(...d.trace.mlp[best].map(norm)) ? r : best), subj[0]);
const span = (kind, row, thr) => { const cs = d.trace[kind][row].map((v, c) => (norm(v) > thr ? c : -1)).filter((c) => c >= 0); return [cs[0], cs.at(-1)]; };
const [m0, m1] = span("mlp", subjLast, 0.3), [a0, a1] = span("attn", last, 0.3);
const mlpPeak = Math.max(...d.trace.mlp[subjLast].map(norm));

// lattice geometry, so paths and notes can point at nodes
const LX = 470, LY = 170, LW = 880, LH = 740, dx = LW / T, dy = LH / L;
const X = (c) => LX + dx * (c + 0.5), Y = (r) => LY + LH - dy * r;

export default explainer({ title: "Where GPT-2 keeps a fact", music: true }, (s) => {
  // ---- 0 · the question
  s.heading("where a model keeps a fact");
  s.sfx("draw");
  s.tokens("prompt", d.tokens, { x: 960, y: 480, size: 50 });
  s.sfx("type", { n: 10 });
  s.wait(300);
  s.together((g) => { g.chip("answer", target, { value: d.clean, x: 960, y: 640, size: 44 }); g.sfx("chime"); });
  s.narrate(`GPT-2 finishes this sentence with “${target}”, at ${pct(d.clean)}.`);
  s.narrate("Somewhere inside it, that fact is stored. Where?");

  // ---- 1 · twenty-four layers
  s.together((g) => {
    g.dial(1, "24 layers", { of: 4 });
    g.heading("every word is a column of numbers");
    g.fade("prompt", 0); g.fade("answer", 0);
    g.sfx("whoosh");
  });
  s.together((g) => {
    g.lattice("lattice", { cols: T, rows: L + 1, x: LX, y: LY, w: LW, h: LH, colLabels: d.tokens, dur: 2200 });
    g.sfx("sweep", { dur: 2200 });
    g.narrate(`Each word becomes a column of numbers. ${L} layers rewrite every column, bottom to top.`);
  });
  s.set("lattice", { flow: 1 }, { dur: 600 });
  s.narrate("Only the last column chooses the next word.");
  s.set("lattice", { hiCol: last }, { dur: 400 });
  s.sfx("tick");

  // ---- 2 · read every layer early (the logit lens)
  s.together((g) => {
    g.dial(2, "logit lens");
    g.heading("read each layer as if it were the last");
    g.set("lattice", { flow: 0.35 }, { dur: 600 });
  });
  const labels = guess.map((g, l) => ({ text: g, hot: g === target, warm: g === "London" }));
  s.set("lattice", { labels }, { dur: 1 });
  s.together((g) => {
    g.set("lattice", { labelUpTo: L }, { dur: 5200, ease: "linear" });
    g.list("guesses", runs.map(runText), { x: 96, y: 300, gap: 50, title: "best guess, last word", dur: 5200 });
    g.chart("track", {
      x: 1490, y: 330, w: 330, h: 300, xMax: L, logY: true, yMin: 1e-5, yMax: 1,
      points: d.targetTrack.map((v, l) => [l, Math.max(v.p, 1e-5)]),
      xTicks: [[0, "0"], [8, "8"], [16, "16"], [24, "24"]], yTicks: [[1, "100%"], [0.01, "1%"], [0.0001, "0.01%"]],
      marks: [{ x: london[0], label: "London", color: "gold" }, { x: firstTop, label: target, color: "accent", dy: 22 }],
      title: `chance of “${target}”, by layer`, dur: 5200,
    });
    g.sfx("sweep", { dur: 5200 });
    g.narrate("So read that column at every layer, as if the model stopped there.", { dur: 2600 });
    g.after(2800, (h) => { h.narrate(`Early layers just say “the”. Around layer ${london[0]} the guess is a city: London.`, { dur: 2500 }); });
  });
  s.together((g) => { g.set("guesses", { active: runs.length - 1 }, { dur: 600 }); g.sfx("chime"); });
  s.narrate(`Only from layer ${firstTop} does it become ${target}. The model narrows down: something like a city first, then the right one.`);

  // ---- 3 · break it, then repair it (causal tracing)
  s.together((g) => {
    g.dial(3, "causal tracing");
    g.heading("break it, then repair it one piece at a time");
    g.clear(["lattice", "guesses", "track"]);
    g.sfx("whoosh");
  });
  s.together((g) => {
    g.tokens("prompt2", d.tokens, { x: 860, y: 215, size: 26, hl: [] });
    g.chip("answer2", target, { value: d.clean, x: 1610, y: 215, size: 26 });
  });
  s.narrate("This tells us when the answer appears, not where it's stored. For that, break the model.");
  s.set("prompt2", { hl: subj }, { dur: 1 });
  s.together((g) => {
    g.set("prompt2", { noise: 1 }, { dur: 600 });
    g.set("answer2", { value: d.trace.pCorrupt }, { dur: 1400 });
    g.sfx("glitch");
    g.narrate(`Scramble the subject with noise, and “${target}” collapses from ${pct(d.clean)} to ${pct(lo)}.`);
  });
  const HX1 = 250, HX2 = 1080, HY = 380, CELL = 28;
  s.together((g) => {
    g.narrate("Now put back one piece of the clean run at a time, and watch which piece brings it back.");
    g.heat("mlp", { x: HX1, y: HY, cell: CELL, values: heat("mlp"), rowLabels: d.tokens, rowHl: subj, hue: "green", title: "putting back an MLP  (the model's memory)", dur: 4200 });
    g.heat("attn", { x: HX2, y: HY, cell: CELL, values: heat("attn"), rowLabels: d.tokens, rowHl: [last], hue: "violet", title: "putting back attention  (moving between words)", dur: 4200 });
    g.sfx("sweep", { dur: 4200 });
  });
  s.text("cols", "layers 1 → 24, left to right · brighter = more of the answer comes back", { x: 960, y: HY + T * (CELL + 2) + 46, size: 20, font: "sans", color: "dim", dur: 900 });
  s.together((g) => {
    g.set("mlp", { focus: { r0: subjLast, r1: subjLast, c0: m0, c1: m1 } }, { dur: 1 });
    g.set("mlp", { focusReveal: 1 }, { dur: 900 });
    g.sfx("tick");
  });
  s.narrate(`The memory that matters sits at “${d.tokens[subjLast].trim()}” — the last piece of “Eiffel”, not “Tower” — around layers ${m0 + 1} to ${m1 + 1}. It alone brings back up to ${Math.round(mlpPeak * 100)}% of the way.`);
  s.together((g) => {
    g.set("attn", { focus: { r0: last, r1: last, c0: a0, c1: a1 } }, { dur: 1 });
    g.set("attn", { focusReveal: 1 }, { dur: 900 });
    g.sfx("tick");
  });
  s.narrate(`Attention matters later, at the last word “${d.tokens[last].trim()}”, from layer ${a0 + 1} on. Putting it back restores ${target} completely.`);

  // ---- 4 · the route
  s.together((g) => {
    g.dial(4, "the route");
    g.heading("the route of one fact");
    g.clear(["prompt2", "answer2", "mlp", "attn", "cols"]);
    g.sfx("whoosh");
  });
  s.lattice("lattice2", { cols: T, rows: L + 1, x: LX, y: LY, w: LW, h: LH, colLabels: d.tokens, colHl: [subjLast, last], dur: 1200, opacity: 0.55 });
  const mid = Math.round((m0 + m1) / 2) + 1, late = Math.round((a0 + a1) / 2) + 1;
  s.together((g) => {
    g.narrate(`So the route is: look the fact up in the memory at “${d.tokens[subjLast].trim()}”, then carry it forward to the last word, which says ${target}.`);
    g.path("route", [[X(subjLast), Y(m0 + 1)], [X(subjLast), Y(mid + 3)], [X(subjLast + 3), Y(late - 2)], [X(last), Y(late)], [X(last), Y(L)], [X(last), LY - 40]], { color: "accent", width: 3, pulses: 4, period: 2600, dur: 2600 });
    g.sfx("rise");
  });
  s.chip("answer3", target, { value: d.clean, x: X(last), y: LY - 70, size: 28 });
  s.note("n1", `MLPs at “${d.tokens[subjLast].trim()}”, layers ${m0 + 1}–${m1 + 1}:\nthe fact is looked up`, { x: X(subjLast) - 40, y: Y(m0 + 1) + 70, to: [X(subjLast), Y(mid)], align: "right", color: "green" });
  s.note("n2", `attention at “${d.tokens[last].trim()}”, layers ${a0 + 1}+:\nthe fact is carried to the end`, { x: X(last) + 120, y: Y(late) + 60, to: [X(last), Y(late)], align: "left", color: "violet" });
  s.narrate("That memory is exactly where ROME edits, to make a model believe the tower is somewhere else.");

  // ---- coda
  s.together((g) => {
    g.clear(["lattice2", "route", "answer3", "n1", "n2", "dial"]);
    g.heading("sources");
  });
  s.together((g) => {
    g.text("src1", "Causal tracing: Meng, Bau, Andonian & Belinkov, Locating and Editing Factual Associations in GPT (2022)", { x: 96, y: 300, size: 24, align: "left", color: "ink" });
    g.text("src2", "Logit lens: nostalgebraist (2020)", { x: 96, y: 350, size: 24, align: "left", color: "ink" });
    g.text("src3", `Data: Model Microscope · ${d.model}, ${L} layers · ten noise draws per cell`, { x: 96, y: 400, size: 24, align: "left", color: "dim" });
    g.sfx("chime");
  });
  s.wait(3200);
});
