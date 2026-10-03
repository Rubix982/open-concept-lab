// Capability 3: pick up, carry while walking, throw to a spot, hand over.
import { story, model, P } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";
const parcel = model("parcel", [P("3003", 4, 0, 0, 0), P("3068b", 14, 0, 3, 0)]);

export default story({ title: "Capability: hold, carry, drop", poster: 7000 }, (s) => {
  s.shot({ at: [12, 5, 6], az: 18, el: 22, dist: 34 }, 0);
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.build(parcel, { as: "parcel", at: [6, 2, 5], from: "above", dur: 400 });
  s.minifig("a", [3, 2, 5.5], { look: { torso: 1, legs: 72, hat: "cap", hatColor: 4 } });
  s.minifig("b", [19, 2, 5.5], { look: { torso: 25, legs: 1, hat: "hair", hatColor: 70 } });
  s.turnTo("b", "a", { dur: 10 });
  s.caption("picks it up");
  s.move("a", [4.6, 2, 5.5], { dur: 700 });
  s.pose("a", "arm-r", 60, { dur: 400 });
  s.hold("a", "r", "parcel", { offset: [0, -1.2, -0.6] });
  s.pose("a", "arm-r", 85, { dur: 400 });
  s.caption("carries it while walking");
  s.move("a", [12, 2, 5.5], { dur: 2200 });
  s.caption("hands it over");
  s.move("b", [14.6, 2, 5.5], { dur: 1200 });
  s.pose("b", "arm-l", 85, { dur: 400 });
  s.hold("b", "l", "parcel", { offset: [0, -1.2, -0.6] });
  s.together((g) => { g.pose("a", "arm-r", 0, { dur: 400 }); g.face("a", "grin"); });
  s.caption("throws it to a spot");
  s.turnTo("b", 90, { dur: 400 });
  s.pose("b", "arm-l", 130, { dur: 250 });
  s.drop("parcel", { to: [19, 2, 9], dur: 1000, arc: 10, spin: [0, 360, 0] });
  s.pose("b", "arm-l", 0, { dur: 400 });
  s.wait(800);
});
