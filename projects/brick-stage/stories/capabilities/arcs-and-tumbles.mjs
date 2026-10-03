// Capability 4: a hat flies from one head onto another's helmet; a tumbling throw.
import { story, model, P } from "../../lib/director.mjs";
import { floor } from "./_floor.mjs";
const block = model("block", [P("3003", 15, 0, 0, 0), P("3003", 4, 0, 3, 0)]);

export default story({ title: "Capability: arcs and tumbles", poster: 5000 }, (s) => {
  s.shot({ at: [11, 6, 6], az: 12, el: 16, dist: 30 }, 0);
  s.build(floor(), { at: [0, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.minifig("bolt", [4, 2, 6], { look: { torso: 71, legs: 1, print: "vest", hat: "hardhat", hatColor: 14, hatTilt: 0.16 } });
  s.minifig("knight", [17, 2, 6], { look: { torso: 71, legs: 72, print: "knight", hat: "knight", hatColor: 71 } });
  s.caption("the hard hat flies onto the knight's helmet, and stays");
  s.face("bolt", "surprised");
  s.hatFly("bolt", { to: "knight", dur: 1300, arc: 14, spin: [360, 540, 0] });
  s.wait(500);
  s.caption("…and rides along when he walks");
  s.move("knight", [17, 2, 9.5], { dur: 1400 });
  s.caption("a tumbling throw, end over end");
  s.build(block, { as: "block", at: [8, 2, 2], from: "above", dur: 400 });
  s.move("block", [15, 2, 2], { dur: 1400, arc: 16, spin: [720, 0, 0] });
  s.sfx("tik");
  s.wait(800);
});
