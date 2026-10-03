// Capability 7: all eight moods, in turn.
import { story, model, P, MOODS } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";
const house = model("house", [P("3001", 4, 0, 0, 0), P("3001", 4, 0, 3, 0), P("3039", 15, 0, 6, 0, 0), P("3039", 15, 2, 6, 0, 0)]);

export default story({ title: "Capability: moods", poster: 3000 }, (s) => {
  s.shot({ at: [12, 4, 6], az: 25, el: 18, dist: 30 }, 0);
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.build(house, { as: "house", at: [9, 2, 5], from: "above", dur: 300 });
  s.minifig("m", [15, 2, 6], { look: { torso: 1, legs: 72, hat: "cap", hatColor: 14 } });
  for (const m of MOODS) { s.caption(m, "MOOD"); s.mood(m, { dur: 900 }); s.wait(1800); }
});
