// Capability test: the vertical format (1080×1920, for Shorts and Reels).
// The same pieces as a wide explainer — heading, dial, tokens, a LEGO chart
// with pinned labels, captions, a transition — laid out for a tall frame.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { explainer } from "../lib/script.mjs";
import { columns, LEGO } from "../lib/brickcharts.mjs";

const d = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../../../../ai/model-microscope/site/data/eiffel.json", import.meta.url)), "utf8"));
const track = d.targetTrack.map((x) => x.p), firstTop = d.targetTrack.findIndex((x) => x.rank === 1), target = d.targetToken.trim();

export default explainer({ title: "Vertical Format", format: "vertical", music: true }, (s) => {
  s.together((g) => {
    g.heading("24 layers, one answer");
    g.dial(1, "vertical", { of: 2 });
    g.tokens("prompt", ["The", " Eiffel", " Tower", " is", " in"], { y: 330, size: 44 });
    g.narrate(`GPT-2 says “${target}”.`, { dur: 1800 });
  });
  s.chip("ans", target, { value: d.clean, y: 450, size: 40 });
  s.together((g) => {
    g.bricks("cols", columns(track, { log: true, min: 1e-5, gap: 0, maxPlates: 27, colors: track.map((_, l) => (l >= firstTop ? LEGO.orange : LEGO.mediumBlue)) }), { y: 520, h: 1080, az: -52, el: 22, dist: "auto", drift: 0.4, dur: 2600 });
    g.sfx("clicks", { dur: 2600 });
    g.narrate("Each column: the chance of Paris at one layer.", { dur: 2800 });
  });
  s.together((g) => {
    g.text("lt", `layer ${firstTop}: ${target}`, { anchor: { obj: "cols", at: `top${firstTop}`, dy: -46 }, size: 30, font: "mono", weight: 600, color: "accent" });
    g.shot("cols", "orbit", { deg: 50, dur: 4200 });
    g.narrate(`From layer ${firstTop} it is the top guess.`, { dur: 2600 });
  });
  s.transition("wipe");
  s.clear(["cols", "lt", "prompt", "ans"], { dur: 1 });
  s.dial(2, "end");
  s.text("end", "1080 × 1920", { y: 960, size: 64, font: "mono", weight: 600 });
  s.wait(1800);
});
