// Capability: spoken narration. Every narrate() is spoken by macOS `say`, the
// scene is paced by the real clips, and the music bed ducks under the voice.
// Data: GPT-2's chance of "Paris", layer by layer (Model Microscope).
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { columns, LEGO } from "../lib/brickcharts.mjs";

const d = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../../../../ai/model-microscope/site/data/eiffel.json", import.meta.url)), "utf8"));
const track = d.targetTrack.map((x) => x.p), L = d.layers, target = d.targetToken.trim();
const firstTop = d.targetTrack.findIndex((x) => x.rank === 1);
const pct = (p) => `${Math.round(p * 100)} percent`;

export default explainer({ title: "Spoken Narration", voice: { name: "Samantha", rate: 185 }, music: true }, (s) => {
  const cols = columns(track, { log: true, min: 1e-5, gap: 0, maxPlates: 27, colors: track.map((_, l) => (l >= firstTop ? LEGO.orange : LEGO.mediumBlue)), cap: track.map((_, l) => (l >= firstTop ? LEGO.yellow : LEGO.white)) });
  s.together((g) => {
    g.heading("a voice, paced by its own clips");
    g.bricks("cols", cols, { az: -14, el: 16, dist: 44, dur: 4000 });
    g.sfx("clicks", { dur: 4000 });
    g.narrate(`Each column is one layer of GPT-2, asked where the Eiffel Tower is.`);
  });
  s.together((g) => {
    g.set("cols", { az: 16 }, { dur: 12000 });
    g.after(0, (q) => {
      q.narrate(`For ${firstTop - 1} layers, ${target} barely registers.`);
      q.text("c1", `layer ${firstTop}: ${target}`, { anchor: { obj: "cols", at: `top${firstTop}`, dy: -40 }, size: 22, font: "mono", weight: 600, color: "accent" });
      q.sfx("chime");
      q.narrate(`Then, at layer ${firstTop}, it jumps to the top guess, and the model ends at ${pct(d.clean)}.`);
    });
  });
  s.narrate("Captions come from the same lines, so the subtitles always match what you hear.", { silent: false });
  s.wait(1200);
});
