// Capability 1: walking a path, turning, looking, waving, leaning.
import { story } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";

export default story({ title: "Capability: walk and gesture", poster: 9000 }, (s) => {
  s.shot({ at: [12, 6, 6], az: 20, el: 26, dist: 40 }, 0);
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 10, dur: 300 });
  s.minifig("walker", [3, 2, 3], { look: { torso: 4, legs: 72, hat: "cap", hatColor: 1 } });
  s.caption("walks a square, facing where it goes");
  s.move("walker", [20, 2, 3], { dur: 2400 });
  s.move("walker", [20, 2, 9], { dur: 1200 });
  s.move("walker", [3, 2, 9], { dur: 2400 });
  s.move("walker", [3, 2, 3], { dur: 1200 });
  s.caption("turns to the camera, looks left and right");
  s.shot({ at: [3, 6, 3], az: 10, el: 10, dist: 14 }, 900);
  s.turnTo("walker", "camera", { dur: 600 });
  s.pose("walker", "head", 50, { dur: 500 }); s.pose("walker", "head", -50, { dur: 700 }); s.pose("walker", "head", 0, { dur: 400 });
  s.caption("waves");
  s.face("walker", "grin");
  for (let k = 0; k < 2; k++) { s.pose("walker", "arm-l", 160, { dur: 300 }); s.pose("walker", "arm-l", 120, { dur: 250 }); }
  s.pose("walker", "arm-l", 0, { dur: 400 });
  s.caption("leans in, twists a wrist");
  s.together((g) => { g.pose("walker", "lean", 25, { dur: 600 }); g.pose("walker", "arm-r", 80, { dur: 600 }); });
  s.pose("walker", "hand-r", 90, { dur: 400 });
  s.together((g) => { g.pose("walker", "lean", 0, { dur: 500 }); g.pose("walker", "arm-r", 0, { dur: 500 }); g.pose("walker", "hand-r", 0, { dur: 500 }); });
  s.wait(600);
});
