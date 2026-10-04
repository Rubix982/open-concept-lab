// Capability test: camera language and transitions.
// One LEGO heat map (GPT-2's causal trace) seen through every shot preset and
// a focus pull; columns with an orbit and handheld drift; bars; and all five
// transitions between the chapters. Data: Model Microscope's Eiffel Tower case.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { heatGrid, columns, barChart, LEGO, RAMPS } from "../lib/brickcharts.mjs";

const d = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../../../../ai/model-microscope/site/data/eiffel.json", import.meta.url)), "utf8"));
const lo = d.trace.pCorrupt, hi = d.clean, norm = (v) => Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
const key = d.trace.corrupt.reduce((b, r) => (Math.max(...d.trace.mlp[r]) > Math.max(...d.trace.mlp[b]) ? r : b), d.trace.corrupt[0]);
const peak = d.trace.mlp[key].indexOf(Math.max(...d.trace.mlp[key]));
const word = d.tokens[key].trim();

export default explainer({ title: "Camera and Transitions", description: "Capability test: shot presets, focus pulls, orbit, drift and the five transitions, on LEGO charts of GPT-2 data.", music: true }, (s) => {
  let n = 0;
  const caption = (text) => s.text(`cap${n++}`, text, { x: 96, y: 1000, size: 22, font: "mono", align: "left", color: "dim", dur: 400 });
  const swap = (text) => { s.fade(`cap${n - 1}`, 0, { dur: 200 }); caption(text); };

  // ---- 1 · one model, every shot
  s.together((g) => {
    g.heading("camera: one model, every shot");
    g.dial(1, "shots", { of: 3 });
    g.bricks("heat", heatGrid(d.trace.mlp.map((r) => r.map(norm)), { ramp: RAMPS.green, maxPlates: 7 }), { az: -20, el: 40, dist: "auto", dur: 3200 });
    g.sfx("clicks", { dur: 3200 });
  });
  caption('s.shot("heat", "hero")');
  s.shot("heat", "hero", { dur: 1800 }); s.wait(500);
  swap(`s.shot("heat", "closeup:cell:${key}:${peak}")`);
  s.together((g) => { g.shot("heat", `closeup:cell:${key}:${peak}`, { dur: 2000 }); g.narrate(`A dolly in on the ridge at “${word}”, layer ${peak + 1}.`, { dur: 2600 }); });
  swap('s.shot("heat", "top")');
  s.shot("heat", "top", { dur: 1800 }); s.wait(500);
  swap('s.shot("heat", "side")');
  s.shot("heat", "side", { dur: 1800 }); s.wait(400);
  swap('s.shot("heat", "wide")');
  s.shot("heat", "wide", { dur: 1600 });

  // ---- 2 · orbit and drift, behind a grid transition
  s.transition("grid");
  s.clear(["heat", `cap${n - 1}`], { dur: 1 });
  const track = d.targetTrack.map((x) => x.p);
  const firstTop = d.targetTrack.findIndex((x) => x.rank === 1);
  s.together((g) => {
    g.heading("orbit and drift");
    g.dial(2, "orbit");
    g.bricks("cols", columns(track, { log: true, min: 1e-5, gap: 0, maxPlates: 27, colors: track.map((_, l) => (l >= firstTop ? LEGO.orange : LEGO.mediumBlue)) }), { az: -30, el: 16, dist: 44, drift: 0.6, dur: 2600 });
    g.sfx("clicks", { dur: 2600 });
  });
  caption('s.shot("cols", "orbit", { deg: 80 }) · drift: 0.6');
  s.together((g) => { g.shot("cols", "orbit", { deg: 80, dur: 6000 }); g.narrate("A slow orbit with a little handheld drift, the same in every render.", { dur: 3400 }); });
  s.transition("iris");
  s.clear(["cols", `cap${n - 1}`], { dur: 1 });

  // ---- 3 · the other transitions
  const says = d.says.slice(0, 5);
  s.together((g) => {
    g.heading("glitch, fold, wipe");
    g.dial(3, "transitions");
    g.bricks("bars", barChart(says.map(([, p]) => p), { colors: [LEGO.orange, LEGO.mediumBlue, LEGO.mediumBlue, LEGO.mediumBlue, LEGO.mediumBlue], maxPlates: 24, gap: 2 }), { az: -24, el: 22, dist: 40, dur: 2200 });
    g.sfx("clicks", { dur: 2200 });
  });
  s.together((g) => says.forEach(([w, p], i) => g.text(`v${i}`, `${w.trim()} ${Math.round(p * 100)}%`, { anchor: { obj: "bars", at: `bar${i}`, dy: -30 }, size: 20, font: "mono", color: i ? "ink" : "accent", dur: 400 })));
  s.wait(800);
  s.transition("glitch"); s.wait(700);
  s.transition("blueprint-fold"); s.wait(700);
  s.transition("wipe");
  s.clear(["bars", ...says.map((_, i) => `v${i}`), "dial"], { dur: 1 });
  s.heading("five transitions · six shots");
  s.text("end", "wipe · iris · grid · glitch · blueprint-fold", { x: 96, y: 300, size: 26, font: "mono", align: "left" });
  s.wait(2200);
});
