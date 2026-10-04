// Capability: math, code and marks. LaTeX writing itself on, a code panel
// with a moving focus, counters, and marks (underline, circle, brace, strike,
// highlight, arrow) pinned to them. The code is the real routing switch from
// the cache-router miniature; the numbers are its default run.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";

const read = (rel) => fs.readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
const goLines = read("../../../../systems/miniatures/sims/cacherouter/cacherouter.go").split("\n");
const at = goLines.findIndex((l) => l.includes("switch p.Policy {"));
const snippet = goLines.slice(at, at + 16).map((l) => l.replace(/^\t\t/, "").replace(/\t/g, "  ")).join("\n");
const line = (needle) => snippet.split("\n").findIndex((l) => l.includes(needle)) + 1;
const baked = read("../../../../systems/miniatures/site/baked/cache-router.js");
const runs = JSON.parse(baked.slice(baked.indexOf("{"), baked.lastIndexOf("}") + 1));
const stats = Object.values(runs)[0].stats;
const ms = (label) => stats.find((x) => x.label === label).ttftP50 * 1000;

export default explainer({ title: "Math, Code and Marks", description: "Capability test: LaTeX, code panels, counters and emphasis marks in the blueprint layer." }, (s) => {
  // ---- math
  s.together((g) => {
    g.heading("math, code and marks");
    g.dial(1, "math", { of: 3 });
    g.math("attn", String.raw`\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^{\top}}{\color{#ff7a59}{\sqrt{d_k}}}\right)V`, { x: 960, y: 400, size: 74, dur: 2600 });
    g.sfx("draw");
    g.narrate("LaTeX, typeset by MathJax and written on like a pen stroke.", { dur: 3000 });
  });
  s.together((g) => {
    g.arrowTo("why", [560, 700], { anchor: { id: "attn", fx: 0.835, fy: 0.84 }, label: "keeps the scores from growing with size", bend: 0.28, size: 24 });
    g.sfx("tick");
    g.narrate("Marks point at a part of it…", { dur: 2200 });
  });
  s.together((g) => {
    g.brace("rows", { anchor: { id: "attn", fx: 0.77, fy: 0.5 }, w: 620, h: 170, depth: 24, label: "a weighted mix of the values", side: "above", gap: 10, color: "cyan" });
    g.narrate("…or gather it with a brace.", { dur: 2000 });
  });
  s.wait(600);
  s.together((g) => g.clear(["attn", "why", "rows"]));

  // ---- code
  s.together((g) => {
    g.dial(2, "code");
    g.code("go", snippet, { lang: "go", x: 120, y: 190, size: 21, title: "sims/cacherouter/cacherouter.go", dur: 2800 });
    g.sfx("type", { n: 14 });
    g.narrate("Code types itself on, with its own syntax colours.", { dur: 3000 });
  });
  const rr = line('"round-robin"'), aff = line('"affinity"'), bnd = line('"bounded"');
  s.together((g) => {
    g.focus("go", [rr, rr + 1, rr + 2]);
    g.count("old", ms("Round robin"), ms("Round robin"), { x: 1500, y: 360, size: 72, format: "ms", label: "round robin · first token, median", dur: 400 });
    g.narrate("Focus moves line by line. Round robin waits this long…", { dur: 2800 });
  });
  s.together((g) => {
    g.focus("go", [aff, aff + 1]);
    g.underline("u1", { anchor: { id: "go", line: aff + 1 }, color: "green" });
    g.strike("x1", { anchor: { id: "old" }, color: "accent" });
    g.count("new", ms("Round robin"), ms("Cache affinity"), { x: 1500, y: 600, size: 72, format: "ms", color: "green", label: "cache affinity", dur: 2000 });
    g.sfx("rise");
    g.narrate("…route by prompt instead, and the counter falls.", { dur: 2600 });
  });
  s.together((g) => {
    g.focus("go", [bnd, bnd + 1, bnd + 2, bnd + 3, bnd + 4, bnd + 5, bnd + 6, bnd + 7]);
    g.highlight("h1", { anchor: { id: "go", line: line("limit :=") }, color: "gold", alpha: 0.18 });
    g.circle("c1", { anchor: { id: "new" }, h: 70, color: "green", pad: 14 });
    g.sfx("chime");
    g.narrate("Highlight a line, circle a number, and every mark draws itself on.", { dur: 3200 });
  });
  s.wait(800);
  s.together((g) => g.clear(["go", "old", "new", "u1", "x1", "h1", "c1"]));

  // ---- counters on their own
  s.together((g) => {
    g.dial(3, "counters");
    g.count("k1", 0, 0.97, { x: 560, y: 500, size: 96, format: "pct", color: "green", label: "prompt found in cache", dur: 2200 });
    g.count("k2", 1, 21, { x: 1360, y: 500, size: 96, format: "x", color: "accent", label: "faster to the first token", dur: 2200 });
    g.sfx("sweep", { dur: 2200 });
    g.narrate("Numbers count up with their units: percent, milliseconds, times.", { dur: 3000 });
  });
  s.together((g) => {
    g.underline("u2", { anchor: { id: "k1" }, color: "green", wavy: true });
    g.brace("b2", { anchor: { id: "k2" }, side: "below", gap: 70, label: "580 ms → 28 ms", color: "accent" });
  });
  s.wait(2400);
});
