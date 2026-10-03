// The Bridge to Gus — Scene 6, "Lights On" (first slice).
// Dusk, a desk lamp's warm cone, a knock at the lighthouse door, and the
// beam sweeping across everyone. See bridge-to-gus.txt.
import { story, model, P } from "../lib/director.mjs";

const GREEN = 2, WHITE = 15, RED = 4, DGRAY = 72, LGRAY = 71, BROWN = 70, PINK = 29, TAN = 19, YELLOW_T = 46, BLUE = 1;

// the far bank: a grey outcrop of slopes on green
const outcrop = model("outcrop", [
  P("3029", GREEN, 0, 0, 0), P("3029", GREEN, 0, 0, 4), P("3029", GREEN, 0, 1, 2),
  P("3001", DGRAY, 3, 2, 3), P("3001", DGRAY, 5, 2, 5),
  P("3039", DGRAY, 1, 2, 3, 270), P("3039", DGRAY, 9, 2, 4, 90), P("3039", DGRAY, 4, 2, 1, 0),
  P("3020", DGRAY, 3, 5, 4), P("3022", LGRAY, 4, 6, 4),
]);
// the lighthouse: red and white round bricks, a trans-yellow lamp on top
const tower = [];
for (let k = 0; k < 6; k++) tower.push(P("3941", k % 2 ? WHITE : RED, 0, k * 3, 0));
const lighthouse = model("lighthouse", [...tower, P("4032b", WHITE, 0, 18, 0), P("3941", YELLOW_T, 0, 19, 0), P("4032b", RED, 0, 22, 0)]);
const cake = model("cake", [P("3941", PINK, 0, 0, 0), P("4032b", WHITE, 0, 3, 0)]);

export default story({ title: "The Bridge to Gus — Scene 6", drift: 0.25 }, (s) => {
  s.shot({ at: [5, 10, 5], az: 28, el: 14, dist: 34 }, 0);
  s.mood("dusk", { dur: 10 });
  s.ambience("room");
  s.light("desk", { kind: "spot", at: [10, 60, 12], target: [5, 8, 4], color: "#ffcf8a", intensity: 1.6, angle: 16, beam: false });
  s.light("beam", { kind: "spot", at: [5, 28, 5], az: 200, reach: 40, drop: 18, angle: 7, color: "#ffe9a8", intensity: 0, shadows: false });
  s.together((g) => {
    g.card("THE BRIDGE TO GUS", "Lights On", { dur: 3000 });
    g.build(outcrop, { at: [0, 0, 0], from: "below", stagger: 30, dur: 400 });
    g.build(lighthouse, { as: "lighthouse", at: [4, 7, 4], from: "above", stagger: 60, dur: 400 });   // on the outcrop's top plate
    g.minifig("gus", [7.5, 2, 1], { facing: 0, look: { torso: BLUE, legs: DGRAY, print: "sweater", hat: "cap", hatColor: BLUE, beard: true, face: "sad" }, dur: 10 });
  });
  s.minifig("bolt", [-6, 0, -6], { facing: 40, look: { torso: LGRAY, legs: 1, print: "vest", face: "worried" }, dur: 10 });
  s.minifig("maribel", [-8, 0, -4], { facing: 40, look: { torso: WHITE, legs: TAN, print: "apron", hat: "hair", hatColor: BROWN, extra: "flour", face: "smile" }, dur: 10 });
  s.build(cake, { as: "cake", at: [-8, 4, -4], from: "above", dur: 10, stagger: 1 });
  s.hold("maribel", "r", "cake", { offset: [0, -1.6, -0.8] });
  s.pose("maribel", "arm-r", 70, { dur: 10 });

  s.together((g) => {
    g.shot({ at: [2, 6, 0], az: 34, el: 10, dist: 30 }, 2600);
    g.move("bolt", [5.5, 0, -1.2], { dur: 2600 });
    g.move("maribel", [3.5, 0, -0.6], { dur: 2600 });
  });
  s.sfx("knock");
  s.wait(900);
  s.together((g) => { g.turn("gus", 180, { dur: 700 }); g.face("gus", "surprised"); });
  s.shot({ at: [5, 7, 0], az: 20, el: 8, dist: 18 }, 1400);
  s.pose("gus", "lean", 14, { dur: 600 });
  s.say("maribel", "It's missing the candle.", { dur: 2000 });
  s.together((g) => { g.turn("gus", -180, { dur: 700 }); g.face("gus", "determined"); });

  // the lamp: a click, the dome blazes, the beam sweeps across them
  s.sfx("switch");
  s.lamp("lighthouse", true, { color: "#ffd36b", intensity: 1.2, dur: 500 });
  s.lightTo("beam", { intensity: 2.2 }, { dur: 500 });
  s.shot({ at: [3, 12, 2], az: -10, el: 18, dist: 42 }, 2500);
  s.lightTo("beam", { az: 560 }, { dur: 7000 });
  s.wait(1600);
  s.together((g) => { g.turn("gus", 180, { dur: 700 }); g.face("gus", "grin"); });
  s.say("gus", "No it's not.", { dur: 1800 });
  s.sfx("cheer");
  s.together((g) => { g.face("bolt", "grin"); g.face("maribel", "grin"); g.move("bolt", [5.5, 0, -1.2], { dur: 700, hop: 1.2, steps: 2 }); });
  s.wait(2600);
  s.fadeOut({ dur: 1500 });
});
