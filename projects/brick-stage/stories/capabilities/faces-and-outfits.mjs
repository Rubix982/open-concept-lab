// Capability 2: every expression, outfit and hat, side by side.
import { story } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";

const EXPR = ["smile", "grin", "neutral", "sad", "worried", "surprised", "determined", "deadpan"];
const OUTFITS = [
  { print: "vest", torso: 71, hat: "hardhat", hatColor: 14 }, { print: "apron", torso: 15, hat: "hair", hatColor: 70, extra: "flour" },
  { print: "sweater", torso: 1, hat: "cap", hatColor: 1, beard: true }, { print: "chef", torso: 15, hat: "chef", hatColor: 15 },
  { print: "firefighter", torso: 4, hat: "firefighter", hatColor: 4 }, { print: "astronaut", torso: 15, hat: "astronaut", hatColor: 15 },
  { print: "knight", torso: 71, hat: "knight", hatColor: 71 }, { print: "none", torso: 25 },
];

export default story({ title: "Capability: faces and outfits", poster: 5000 }, (s) => {
  s.build(floor(19), { at: [0, 0, 0], from: "below", stagger: 5, dur: 200 });
  EXPR.forEach((e, i) => s.minifig(`face-${e}`, [2.5 + i * 2.7, 2, 3], { look: { torso: 15, legs: 72, face: e }, dur: 10 }));
  OUTFITS.forEach((o, i) => s.minifig(`outfit-${i}`, [2.5 + i * 2.7, 2, 9], { look: { legs: 72, ...o }, dur: 10 }));
  s.caption("expressions (front) and outfits (back)");
  s.shot({ at: [12, 5, 4], az: 0, el: 14, dist: 30 }, 0);
  s.wait(2500);
  s.shot({ at: [8, 4.5, 3], az: 0, el: 6, dist: 14 }, 1500);
  s.wait(2000);
  s.caption("outfits and hats");
  s.shot({ at: [12, 5, 9], az: 0, el: 34, dist: 24 }, 1500);
  s.wait(2000);
});
