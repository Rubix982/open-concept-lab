// Test Chamber — a clinical instruction video in the style of a puzzle-game
// tutorial. The room, button, door and signal line are set pieces; the test
// object is a LEGO model, checked by brick-check like every other model.
import { story, model, P } from "../lib/director.mjs";

const GRAY = 71, DARK = 72, ORANGE = 25;
const cube = model("test-object", [
  P("3001", GRAY, 0, 0, 0), P("3001", GRAY, 0, 0, 2),
  P("3001", DARK, 0, 3, 0, 90), P("3001", DARK, 2, 3, 0, 90),   // a dark band, crossing the layer below
  P("3001", GRAY, 0, 6, 0), P("3001", GRAY, 0, 6, 2),
  P("3031", GRAY, 0, 9, 0),
  P("3068b", ORANGE, 1, 10, 1),
  P("3069b", GRAY, 0, 10, 0), P("3069b", GRAY, 2, 10, 0), P("3069b", GRAY, 0, 10, 3), P("3069b", GRAY, 2, 10, 3),
  P("3069b", GRAY, 0, 10, 1, 90), P("3069b", GRAY, 3, 10, 1, 90),
]);

const WIRE = [[14.5, 0, 12], [18, 0, 12], [18, 0, 27], [34, 0, 27], [34, 0, 36], [34, 24, 36], [40, 24, 36]];

export default story({ title: "Test Chamber", drift: 0.6 }, (s) => {
  s.shot({ at: [24, 4, 18], az: -30, el: 34, dist: 92 }, 0);
  s.caption("Test Chamber 01", "CONSTRUCTION");
  s.shot({ at: [23, 6, 17], az: -34, el: 27, dist: 74 }, 8000);
  s.room({ w: 48, d: 36, h: 30, dur: 7600 });

  s.caption("Install the button.", "STEP 01");
  s.shot({ at: [16, 3, 14], az: -26, el: 30, dist: 46 }, 1400);
  s.button("button", [12, 0, 12]);
  s.wait(400);
  s.caption("Install the exit.", "STEP 02");
  s.shot({ at: [34, 8, 26], az: -18, el: 18, dist: 48 }, 1500);
  s.wait(600);
  s.door("exit", { x: 36, width: 8, height: 20 });
  s.caption("Connect them.", "STEP 03");
  s.together((g) => {
    g.shot({ at: [24, 5, 20], az: -30, el: 32, dist: 66 }, 1800);
    g.signal("wire", WIRE, { dur: 2800 });
  });

  s.caption("Assemble the test object.", "STEP 04");
  s.shot({ at: [6, 3, 22], az: -24, el: 22, dist: 30 }, 1500);
  s.build(cube, { as: "cube", at: [3, 0, 21], from: "everywhere", stagger: 120 });
  s.wait(300);

  s.caption("Introduce the subject.", "STEP 05");
  s.shot({ at: [20, 4, 14], az: -30, el: 28, dist: 56 }, 1500);
  s.figure("subject", [24, 0, 5]);
  s.wait(500);

  s.caption("The subject attempts the test.", "TRIAL 1");
  s.move("subject", [12, 1.4, 12], { dur: 2300 });
  s.press("button");
  s.together((g) => { g.activate("wire"); g.open("exit"); });
  s.wait(300);
  s.together((g) => {
    g.release("button"); g.deactivate("wire"); g.close("exit", { dur: 1100 });
    g.move("subject", [27, 0, 24], { dur: 2300 });
  });
  s.caption("Insufficient.", "TRIAL 1");
  s.turn("subject", -140, { dur: 800 });
  s.wait(900);

  s.caption("The subject uses the test object.", "TRIAL 2");
  s.shot({ at: [12, 3, 18], az: -22, el: 26, dist: 44 }, 1800);
  s.move("subject", [9, 0, 23], { dur: 2600 });
  s.move("cube", [3, 7, 21], { dur: 600, hop: 0 });
  s.together((g) => {
    g.move("subject", [13, 0, 17], { dur: 2000 });
    g.move("cube", [8, 7, 15], { dur: 2000, hop: 0 });
  });
  s.move("cube", [10, 1.2, 10], { dur: 700, hop: 0 });
  s.press("button");
  s.together((g) => { g.activate("wire"); g.open("exit"); });

  s.caption("The subject completes the test.", "TRIAL 2");
  s.shot({ at: [30, 6, 26], az: -26, el: 22, dist: 56 }, 2500);
  s.move("subject", [30, 0, 27], { dur: 2200 });
  s.move("subject", [40, 0, 33], { dur: 1500 });
  s.move("subject", [40, 0, 41], { dur: 1200 });
  s.close("exit");
  s.shot({ at: [24, 6, 18], az: -32, el: 30, dist: 78 }, 2600);
  s.caption("Test Chamber 01", "COMPLETE");
  s.wait(3200);
});
