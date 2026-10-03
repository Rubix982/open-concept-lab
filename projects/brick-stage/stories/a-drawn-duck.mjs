// A Drawn Duck — made by showcase.mjs from duck.glb (drawn by hand, made 3D by InstantMesh (Apache-2.0)).
// Edit freely: add captions, characters, moods. Then: node build.mjs a-drawn-duck
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { story, model } from "../lib/director.mjs";

const data = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../models/a-drawn-duck.json", import.meta.url)), "utf8"));
const STAGGER = 33;          // ms between parts: the whole build takes ~12 s
// section k of the model, as its own model (shifted down if it's built on its own)
const part = (k, id, base = 0) => { const s = data.sections[k]; return model(id, data.parts.slice(s.from, s.to).map((p) => ({ ...p, y: p.y - base }))); };

export default story({
  title: "A Drawn Duck", drift: 0.4,
  sources: ["Shape: drawn by hand, made 3D by InstantMesh (Apache-2.0)"],
}, (s) => {
  s.shot({ at: [6, 16, 7], az: 30, el: 18, dist: 31 }, 0);
  s.card("A BRICK MODEL OF", "A Drawn Duck", { sub: "364 LEGO plates · drawn by hand, made 3D by InstantMesh (Apache-2.0)" });

  s.section("The whole model");
  s.shot({ at: [6, 16, 7], az: 20, el: 18, dist: 31 }, 2000);
  s.build(part(0, "base"), { at: [0, 0, 0], from: "path", stagger: STAGGER });

  s.caption("364 plates. Checked on a computer, not yet with real bricks.");
  s.wait(2400);
  s.clearCaption();
  s.turnaround("base", { dur: 7000, el: 12, dist: 34, offset: [0, 16, 0] });
  s.wait(7000);
});
