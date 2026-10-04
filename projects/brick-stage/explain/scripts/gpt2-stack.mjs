// One fact, climbing 24 layers — the GPT-2 explainer in 3D: the layers as a
// stack of glowing plates, the camera orbiting, 2D labels pinned to the plates.
// Every number comes from Model Microscope's Eiffel Tower results.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";

const d = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../../../../ai/model-microscope/site/data/eiffel.json", import.meta.url)), "utf8"));
const T = d.tokens.length, L = d.layers, last = T - 1, target = d.targetToken.trim();
const pct = (p) => (p >= 0.1 ? `${Math.round(p * 100)}%` : `${(p * 100).toFixed(1)}%`);
const lo = d.trace.pCorrupt, hi = d.clean, norm = (v) => Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
const guess = d.lens.map((layer) => layer[last][0][0].trim());
const firstTop = d.targetTrack.findIndex((x) => x.rank === 1);
const london = guess.map((g, l) => (g === "London" ? l : -1)).filter((l) => l >= 0);
const subj = d.trace.corrupt;
const key = subj.reduce((b, r) => (Math.max(...d.trace.mlp[r].map(norm)) > Math.max(...d.trace.mlp[b].map(norm)) ? r : b), subj[0]);
const span = (kind, row, thr) => { const cs = d.trace[kind][row].map((v, c) => (norm(v) > thr ? c : -1)).filter((c) => c >= 0); return [cs[0], cs.at(-1)]; };
const [m0, m1] = span("mlp", key, 0.3), [a0, a1] = span("attn", last, 0.3);
// trace column c is block c+1, which writes the stack's row c+1
const M0 = m0 + 1, M1 = m1 + 1, A0 = a0 + 1, A1 = a1 + 1, mid = Math.round((M0 + M1) / 2), late = Math.round((A0 + A1) / 2);
const word = (i) => d.tokens[i].trim();

export default explainer({ title: "One fact, climbing 24 layers", description: "GPT-2's layers as a 3D stack: where 'the Eiffel Tower is in Paris' is looked up and carried to the answer.", music: true }, (s) => {
  s.together((g) => {
    g.heading("one fact, climbing 24 layers");
    g.stage3d("stack", { rows: L + 1, cols: T, colLabels: d.tokens, az: -38, el: 14, dist: 30, dur: 3600 });
    g.sfx("rise");
    g.narrate(`Ask GPT-2 where the Eiffel Tower is, and ${pct(d.clean)} of its bet goes on ${target}.`, { dur: 3600 });
  });
  // a slow orbit under everything that follows
  s.together((g) => {
    g.set("stack", { az: 34 }, { dur: 52000, ease: "inout" });
    g.after(0, (q) => {
      q.dial(1, "the stack", { of: 4 });
      q.narrate(`Each word is a column through ${L} layers; each layer rewrites every column.`);
      q.set("stack", { hiCol: last }, { dur: 500 });
      q.sfx("tick");
      q.narrate("The last column decides what comes next. So read it at every layer.");

      // logit lens, climbing
      q.together((h) => {
        h.dial(2, "logit lens");
        h.set("stack", { labels: guess.map((t) => ({ text: t, hot: t === target, warm: t === "London" })) }, { dur: 1 });
      });
      q.together((h) => {
        h.set("stack", { labelUpTo: L, scan: L }, { dur: 6500, ease: "linear" });
        h.sfx("sweep", { dur: 6500 });
        h.narrate(`It starts as “the”, becomes London around layer ${london[0]}…`, { dur: 3400 });
        h.after(3400, (k) => k.narrate(`…and only from layer ${firstTop} is it ${target}.`, { dur: 3100 }));
      });
      q.set("stack", { scan: -1 }, { dur: 1 });

      // causal tracing, as glowing nodes
      q.together((h) => {
        h.dial(3, "causal tracing");
        h.set("stack", { labelUpTo: -1 }, { dur: 600 });
        h.set("stack", { glow: [{ col: key, r0: M0, r1: M1, color: "green" }] }, { dur: 1 });
        h.sfx("glitch");
        h.narrate(`Scramble “Eiffel” and the answer falls to ${pct(lo)}. Restore one piece at a time:`);
      });
      q.together((h) => {
        h.note("nm", `MLPs at “${word(key)}”, layers ${M0}–${M1}\nthe fact is looked up`, { anchor: { obj: "stack", col: key, row: mid, ox: -300, oy: 110 }, align: "right", color: "green", dur: 900 });
        h.sfx("tick");
        h.narrate(`the memory at “${word(key)}”, the end of “Eiffel”, brings it most of the way back…`);
      });
      q.together((h) => {
        h.set("stack", { glow: [{ col: key, r0: M0, r1: M1, color: "green" }, { col: last, r0: A0, r1: A1, color: "violet" }] }, { dur: 1 });
        h.note("na", `attention at “${word(last)}”, layers ${A0}–${A1}\ncarries it to the end`, { anchor: { obj: "stack", col: last, row: late, ox: 280, oy: 70 }, align: "left", color: "violet", dur: 900 });
        h.sfx("tick");
        h.narrate(`…and attention at the last word, from layer ${A0} on, finishes the job.`);
      });

      // the route
      q.together((h) => {
        h.dial(4, "the route");
        h.set("stack", { route: [[key, M0], [key, M1], [key + 2.5, late - 2], [last, late], [last, L]] }, { dur: 1 });
        h.set("stack", { routeK: 1 }, { dur: 3200, ease: "inout" });
        h.set("stack", { el: 24, dist: 33 }, { dur: 3200 });
        h.sfx("rise");
        h.narrate("Looked up in one place, carried to another, and out comes the answer.", { dur: 3600 });
      });
      q.together((h) => {
        h.chip("ans", target, { value: d.clean, anchor: { obj: "stack", col: last, row: L, dy: -56 }, size: 30 });
        h.sfx("chime");
      });
      q.narrate("That memory is the spot ROME edits to move the tower somewhere else.");
    });
  });
  s.together((g) => {
    g.clear(["stack", "nm", "na", "ans", "dial"]);
    g.heading("sources");
  });
  s.together((g) => {
    g.text("src1", "Causal tracing: Meng, Bau, Andonian & Belinkov, Locating and Editing Factual Associations in GPT (2022)", { x: 96, y: 300, size: 24, align: "left" });
    g.text("src2", "Logit lens: nostalgebraist (2020)", { x: 96, y: 350, size: 24, align: "left" });
    g.text("src3", `Data: Model Microscope · ${d.model}, ${L} layers`, { x: 96, y: 400, size: 24, align: "left", color: "dim" });
    g.sfx("chime");
  });
  s.wait(3000);
});
