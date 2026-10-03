// Rated for Two — the units from The Little Builder, at sunset.
// One builds a flower and offers it; the other builds a heart. Every model is
// checked by brick-check; the arms and heads move on joints (artistic licence:
// the real build would need hinges there).
import { story, model, P } from "../lib/director.mjs";
import { robot } from "./cast/robot.mjs";

const WHITE = 15, LGRAY = 71, DGRAY = 72, ORANGE = 25, BLUE = 1, RED = 4, GREEN = 2, YELLOW = 14,
  BROWN = 70, DPINK = 5, PINK = 29, TAN = 19;

// A flower in a pot: round bricks for the pot and stem, a pink bloom.
const flower = model("flower", [
  P("3062b", BROWN, 0, 0, 0),                                     // pot
  P("3062b", GREEN, 0, 3, 0), P("3062b", GREEN, 0, 6, 0),         // stem
  P("3022", DPINK, 0, 9, 0),                                      // bloom
  P("98138", YELLOW, 0, 10, 0),                                   // its centre
  P("6141", PINK, 1, 10, 0), P("6141", PINK, 0, 10, 1), P("6141", PINK, 1, 10, 1),
]);

// A pixel heart standing on a white base, one stud deep, seams staggered.
const heart = model("heart", [
  P("3034", WHITE, 0, 0, 0),                                      // base, 2 x 8
  P("3005", RED, 3, 1, 0),                                        // row 0: the point
  P("3622", RED, 2, 4, 0),                                        // row 1
  P("3622", RED, 1, 7, 0), P("3004", RED, 4, 7, 0),               // row 2
  P("3010", RED, 0, 10, 0), P("3622", RED, 4, 10, 0),             // row 3
  P("3622", RED, 0, 13, 0), P("3010", RED, 3, 13, 0),             // row 4
  P("3004", RED, 1, 16, 0), P("3004", RED, 4, 16, 0),             // row 5: the two bumps
]);

// A garden path for them to stand on: two layers of tan plates, the top
// layer's seam (x 12) crossing the bottom layer's (x 8, 16) so it holds together.
const path = model("path", [
  P("3034", TAN, 0, 0, 0), P("3034", TAN, 8, 0, 0), P("3034", TAN, 16, 0, 0),
  P("2445", TAN, 0, 1, 0), P("2445", TAN, 12, 1, 0),
]);

export default story({ title: "Rated for Two", poster: 21800, drift: 0.5 }, (s) => {
  s.music("romance");
  s.shot({ at: [0, 12, -6], az: 8, el: 12, dist: 50 }, 0);
  // the stage assembles behind the opening card
  s.together((g) => {
    g.card("PROCEDURE 07", "Express affection.", { dur: 3600 });
    g.build(path, { at: [-12, 0, -8], from: "below", stagger: 60, dur: 500 });
    g.build(robot("unit", ORANGE), { as: "unit", at: [-12, 2, -8], from: "above", stagger: 40, dur: 500 });
    g.build(robot("unit-2", BLUE), { as: "unit-2", at: [6, 2, -8], from: "above", stagger: 40, dur: 500 });
  });

  s.letterbox(true);
  s.mood("sunset", { dur: 5000 });
  s.caption("Sunset. The unit has a request.");
  s.shot({ at: [-2, 12, -7], az: 4, el: 10, dist: 46 }, 3000);
  s.pose("unit", "head", 30, { dur: 500 });
  s.wait(500);
  s.pose("unit", "head", 0, { dur: 400 });
  s.move("unit", [-6, 2, -8], { dur: 1600, hop: 0.6 });

  s.caption("Assemble a flower.", "STEP 01");
  s.shot({ at: [-3, 10, -10], az: -6, el: 12, dist: 32 }, 1500);
  s.build(flower, { at: [-2, 0, -12], from: "everywhere", stagger: 150 });
  s.callout("Flower, potted", { on: "flower", dur: 1800 });
  s.wait(600);

  s.caption("Present the flower.", "STEP 02");
  s.together((g) => {
    g.pose("unit", "right-arm", 80, { dur: 700 });
    g.move("flower", [-2, 6, -11.5], { dur: 700, hop: 0 });
  });
  s.together((g) => {
    g.move("unit", [-3, 2, -8], { dur: 1500, hop: 0.4 });
    g.move("flower", [1, 6, -11.5], { dur: 1500, hop: 0 });
    g.shot({ at: [2, 13, -8], az: 2, el: 8, dist: 38 }, 1500);
  });
  s.say("unit", "For you.", { dur: 1800 });
  s.pose("unit-2", "head", -40, { dur: 500 });
  s.together((g) => { g.highlight("unit-2", { dur: 1800, color: "#ff5a8a" }); g.say("unit-2", "!", { dur: 1000 }); });
  s.emit("hearts", { on: "unit-2", count: 12 });
  s.together((g) => {
    g.pose("unit-2", "left-arm", 75, { dur: 700 });
    g.move("flower", [5, 6, -11.5], { dur: 700, hop: 0 });
    g.pose("unit", "right-arm", 0, { dur: 700 });
  });
  s.caption("Affection: received.");
  s.wait(1600);

  s.caption("Assemble a monument.", "STEP 03");
  // they step apart to make room
  s.together((g) => {
    g.move("unit", [-9, 2, -8], { dur: 1300, hop: 0.4 });
    g.move("unit-2", [11, 2, -8], { dur: 1300, hop: 0.4 });
    g.move("flower", [10, 6, -11.5], { dur: 1300, hop: 0 });
    g.pose("unit-2", "head", 0, { dur: 600 });
  });
  s.together((g) => {
    g.mood("night", { dur: 5000 });
    g.shot({ at: [2, 14, -4], az: -4, el: 12, dist: 52 }, 2500);
    g.build(heart, { at: [-2, 0, -6], from: "everywhere", stagger: 170 });
  });
  s.emit("sparkles", { on: "heart", count: 22, dur: 3000 });
  s.highlight("heart", { dur: 4200, color: "#ff3355" });
  s.together((g) => {
    g.pose("unit", "head", 30, { dur: 600 });
    g.pose("unit-2", "head", -30, { dur: 600 });
  });
  s.together((g) => {
    g.emit("hearts", { on: "unit", count: 10 });
    g.emit("hearts", { on: "unit-2", count: 10 });
  });
  s.caption("Shelter rated for two.");
  s.shot({ at: [2, 20, -4], az: -14, el: 3, dist: 54 }, 4000);   // tilt up to the stars
  s.wait(4000);
  s.clearCaption();
  s.fadeOut({ dur: 1500 });
  s.letterbox(false, { dur: 10 });
  s.card("END OF PROCEDURE", "Affection expressed.", { dur: 3400 });
  s.music(null);
});
