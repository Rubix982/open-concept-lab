// Capability 6: a pool of sunlight slides across the floor; a cloud dims everything.
import { story } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";

export default story({ title: "Capability: sunlight and clouds", poster: 4000 }, (s) => {
  s.shot({ at: [12, 3, 6], az: 15, el: 30, dist: 34 }, 0);
  s.mood("morning", { dur: 10 });
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.minifig("m", [12, 2, 6], { look: { torso: 15, legs: 72, hat: "hair", hatColor: 70 } });
  s.light("sun", { kind: "patch", at: [5, 2, 6], size: [9, 6], color: "#ffe2a0", intensity: 1 });
  s.caption("morning sun through a window, sliding across the floor");
  s.lightTo("sun", { at: [19, 2, 6] }, { dur: 4000, wait: true });
  s.caption("a cloud passes");
  s.together((g) => { g.mood("overcast", { dur: 1500 }); g.lightTo("sun", { intensity: 0.05 }, { dur: 1500 }); g.face("m", "worried"); g.wait(2200); });
  s.caption("and the light comes back, amber now");
  s.together((g) => { g.mood("amber", { dur: 2000 }); g.lightTo("sun", { intensity: 1, color: "#ffa64a", size: [12, 5] }, { dur: 2000 }); g.face("m", "smile"); g.wait(2600); });
});
