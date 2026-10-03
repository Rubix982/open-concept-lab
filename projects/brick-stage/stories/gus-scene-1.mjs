// The Bridge to Gus — Scene 1, "Morning in Baseplate Town" (first slice).
// The bakery, Gus's cake, and Bolt's round-hands problem. See bridge-to-gus.txt.
import { story, model, P } from "../lib/director.mjs";

const GREEN = 2, WHITE = 15, RED = 4, BROWN = 70, PINK = 29, ORANGE_T = 57, LGRAY = 71, TAN = 19, DTAN = 28;

// a patch of baseplate town: two layers of green plates, seams crossed
const ground = model("ground", [
  P("3029", GREEN, 0, 0, 0), P("3029", GREEN, 12, 0, 0), P("3029", GREEN, 0, 0, 4), P("3029", GREEN, 12, 0, 4),
  P("3029", GREEN, 0, 0, 8), P("3029", GREEN, 12, 0, 8),
  P("2445", GREEN, 6, 1, 0), P("3029", GREEN, 6, 1, 2), P("3029", GREEN, 6, 1, 6), P("2445", GREEN, 6, 1, 10),
  P("3795", GREEN, 0, 1, 0), P("3032", GREEN, 0, 1, 2), P("3032", GREEN, 0, 1, 6), P("3795", GREEN, 0, 1, 10),
  P("3795", GREEN, 18, 1, 0), P("3032", GREEN, 18, 1, 2), P("3032", GREEN, 18, 1, 6), P("3795", GREEN, 18, 1, 10),
  // grey tile road along the front
  P("2431", LGRAY, 0, 2, 0), P("2431", LGRAY, 4, 2, 0), P("2431", LGRAY, 8, 2, 0), P("2431", LGRAY, 12, 2, 0), P("2431", LGRAY, 16, 2, 0), P("2431", LGRAY, 20, 2, 0),
  P("2431", LGRAY, 0, 2, 1), P("2431", LGRAY, 4, 2, 1), P("2431", LGRAY, 8, 2, 1), P("2431", LGRAY, 12, 2, 1), P("2431", LGRAY, 16, 2, 1), P("2431", LGRAY, 20, 2, 1),
]);

// the bakery: a counter in front of a back wall with a red sloped roof edge
const bakery = model("bakery", [
  // counter
  P("3009", BROWN, 7, 2, 5), P("3009", BROWN, 7, 2, 6), P("3009", BROWN, 7, 5, 5), P("3009", BROWN, 7, 5, 6),
  P("3795", TAN, 7, 8, 5),
  // back wall
  P("3009", WHITE, 4, 2, 10), P("3009", WHITE, 10, 2, 10), P("3009", WHITE, 7, 5, 10), P("3622", WHITE, 4, 5, 10), P("3622", WHITE, 13, 5, 10),
  P("3009", WHITE, 4, 8, 10), P("3009", WHITE, 10, 8, 10), P("3009", WHITE, 7, 11, 10), P("3622", WHITE, 4, 11, 10), P("3622", WHITE, 13, 11, 10),
  P("3009", WHITE, 4, 14, 10), P("3009", WHITE, 10, 14, 10),
  // red roof edge: slopes facing the street
  P("3039", RED, 4, 17, 10), P("3039", RED, 6, 17, 10), P("3039", RED, 8, 17, 10), P("3039", RED, 10, 17, 10), P("3039", RED, 12, 17, 10), P("3039", RED, 14, 17, 10),
]);

// Gus's cake: a pink round brick, a white round plate, one trans-orange flame
const cake = model("cake", [P("3941", PINK, 0, 0, 0), P("4032b", WHITE, 0, 3, 0), P("6141", ORANGE_T, 0, 4, 0)]);

export default story({ title: "The Bridge to Gus — Scene 1", drift: 0.3 }, (s) => {
  s.shot({ at: [10, 8, 4], az: 18, el: 12, dist: 34 }, 0);
  s.mood("morning", { dur: 10 });
  s.together((g) => {
    g.card("THE BRIDGE TO GUS", "Morning in Baseplate Town", { dur: 3000 });
    g.build(ground, { at: [0, 0, 0], from: "below", stagger: 20, dur: 400 });
    g.build(bakery, { onto: "ground", from: "above", stagger: 25, dur: 400 });
    g.build(cake, { as: "cake", at: [9, 9, 5], from: "above", stagger: 60, dur: 400 });
    g.minifig("maribel", [10, 2, 8.5], { look: { torso: WHITE, legs: TAN, print: "apron", hat: "hair", hatColor: BROWN, face: "smile", extra: "flour" } });
  });

  // Bolt bursts in
  s.minifig("bolt", [0.5, 2, 3.2], { facing: 90, look: { torso: LGRAY, legs: 1, print: "vest", hat: "hardhat", hatColor: 14, hatTilt: 0.16, face: "grin" }, dur: 10 });
  s.shot({ at: [8, 7, 4], az: 24, el: 10, dist: 24 }, 1800);
  s.move("bolt", [9.5, 2, 3.4], { dur: 1500 });
  s.turn("bolt", 90, { dur: 400 });                     // faces the counter
  s.say("bolt", "Is it ready?", { dur: 1500 });
  s.together((g) => { g.face("maribel", "deadpan"); g.say("maribel", "It's Gus's birthday cake, not a rocket.", { dur: 2600 }); });
  s.together((g) => { g.face("maribel", "smile"); g.say("maribel", "Yes. It's ready.", { dur: 1500 }); });

  // the hands: from above, from the side, then the wrist
  s.shot({ at: [10, 8, 4], az: 60, el: 14, dist: 16 }, 1400);
  s.face("bolt", "determined");
  s.pose("bolt", "arm-r", 80, { dur: 500 });
  s.wait(300);
  s.pose("bolt", "arm-r", 20, { dur: 400 });
  s.together((g) => { g.pose("bolt", "arm-r", 70, { dur: 500 }); g.pose("bolt", "hand-r", 90, { dur: 500 }); });
  s.wait(300);
  s.together((g) => { g.pose("bolt", "lean", 22, { dur: 600 }); g.pose("bolt", "arm-r", 95, { dur: 600 }); g.pose("bolt", "hand-r", 0, { dur: 600 }); });
  s.hold("bolt", "r", "cake", { offset: [0.5, -2.6, -0.9] });  // by the flame: the cake hangs out in front of him
  s.together((g) => { g.pose("bolt", "lean", 0, { dur: 700 }); g.pose("bolt", "arm-r", 100, { dur: 700 }); g.face("bolt", "grin"); });
  s.move("bolt", [9.5, 2, 2.6], { dur: 700 });          // steps back so the cake swings clear of the counter

  s.shot({ at: [9, 8, 4], az: 30, el: 10, dist: 20 }, 1200);
  s.together((g) => { g.face("maribel", "surprised"); g.say("maribel", "That's the fire part, Bolt.", { dur: 2000 }); });
  s.say("bolt", "It's the only round part.", { dur: 2200 });
  s.face("maribel", "deadpan");
  s.wait(1200);
});
