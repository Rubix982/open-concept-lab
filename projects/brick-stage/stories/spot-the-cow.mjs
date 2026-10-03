// Spot the Cow — made by showcase.mjs from spot_textured.obj (Spot by Keenan Crane, CC0).
// Edit freely: add captions, characters, moods. Then: node build.mjs spot-the-cow
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { story, model } from "../lib/director.mjs";

const data = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../models/spot-the-cow.json", import.meta.url)), "utf8"));
const STAGGER = 22;          // ms between parts: the whole build takes ~12 s
// section k of the model, as its own model (shifted down if it's built on its own)
const part = (k, id, base = 0) => { const s = data.sections[k]; return model(id, data.parts.slice(s.from, s.to).map((p) => ({ ...p, y: p.y - base }))); };

export default story({
  title: "Spot the Cow", drift: 0.4,
  sources: ["Shape: Spot by Keenan Crane, CC0"],
}, (s) => {
  s.shot({ at: [9, 20, 5], az: 30, el: 18, dist: 41 }, 0);
  s.card("A BRICK MODEL OF", "Spot the Cow", { sub: "543 LEGO plates · Spot by Keenan Crane, CC0" });

  s.section("The whole model");
  s.shot({ at: [9, 20, 5], az: 20, el: 18, dist: 41 }, 2000);
  s.build(part(0, "base"), { at: [0, 0, 0], from: "path", stagger: STAGGER });

  s.caption("543 plates. Checked on a computer, not yet with real bricks.");
  s.wait(2400);
  s.clearCaption();
  s.turnaround("base", { dur: 7000, el: 12, dist: 45, offset: [0, 20, 0] });
  s.wait(7000);
});
