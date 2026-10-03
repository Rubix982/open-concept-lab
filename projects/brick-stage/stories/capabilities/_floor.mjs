// A plain floor for capability tests: two layers of plates, seams crossed.
import { model, P } from "../../lib/director.mjs";
export const floor = (color = 2) => model("floor", [
  P("3029", color, 0, 0, 0), P("3029", color, 12, 0, 0), P("3029", color, 0, 0, 4), P("3029", color, 12, 0, 4), P("3029", color, 0, 0, 8), P("3029", color, 12, 0, 8),
  P("2445", color, 6, 1, 0), P("3029", color, 6, 1, 2), P("3029", color, 6, 1, 6), P("2445", color, 6, 1, 10),
  P("3795", color, 0, 1, 0), P("3032", color, 0, 1, 2), P("3032", color, 0, 1, 6), P("3795", color, 0, 1, 10),
  P("3795", color, 18, 1, 0), P("3032", color, 18, 1, 2), P("3032", color, 18, 1, 6), P("3795", color, 18, 1, 10),
]);
