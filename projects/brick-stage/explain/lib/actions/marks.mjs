// Script verbs for math, code, counters and emphasis marks (drawn by
// lib/plugins/marks.js). A mark goes around a box { x, y, w, h }, or around
// a target given as `anchor`: a 3D point { obj, at } / { obj, col, row }, a
// point in another object { id, fx, fy } (fractions of its bounds), or a line
// of a code panel { id, line }.
export function install(s, { add, span, tl }) {
  /** LaTeX, typeset by MathJax, writing itself on left to right. */
  s.math = (id, tex, o = {}) => add(id, "math", { tex, x: 960, y: 540, size: 64, color: "ink", align: "center", ...o }, o.dur ?? 1400);

  /** A code panel. lang: go | js | python. focus: line numbers (1-based). */
  s.code = (id, source, o = {}) => {
    const lines = source.split("\n").length, focus = o.focus || [];
    return add(id, "code", {
      source, lang: "js", x: 200, y: 200, size: 22, title: "", focus,
      focusAt: focus.length ? Math.min(...focus) : 0, focusSpan: focus.length ? Math.max(...focus) - Math.min(...focus) + 1 : 1, ...o,
    }, o.dur ?? Math.min(4000, 140 * lines));
  };
  /** Move a code panel's focus to these lines (the bar slides there). */
  s.focus = (id, lines, o = {}) => s.set(id, { focus: lines, focusAt: Math.min(...lines), focusSpan: Math.max(...lines) - Math.min(...lines) + 1 }, { dur: o.dur ?? 500 });

  /** A number ticking from one value to another. format: int | comma | ms | pct | x | s | fixed1 | fixed2. */
  s.count = (id, from, to, o = {}) => {
    const t0 = s.t, dur = o.dur ?? 1600;
    add(id, "counter", { value: from, x: 960, y: 540, size: 72, format: "int", color: "ink", align: "center", label: "", ...o }, dur);
    tl.tweens.push({ id, prop: "value", to, t0, t1: t0 + dur, ease: o.ease || "inout" });
    return s;
  };

  // emphasis marks
  const mark = (type, defaults, dur) => (id, o = {}) => add(id, type, { x: 960, y: 540, color: "accent", ...defaults, ...o }, o.dur ?? dur);
  s.underline = mark("underline", {}, 600);
  s.strike = mark("strike", {}, 450);
  s.circle = mark("circle", {}, 800);
  s.highlight = mark("highlight", {}, 500);
  /** A curly brace on one side (below | above | left | right) with a label. */
  s.brace = mark("brace", { side: "below", label: "" }, 800);
  /** A curved arrow from (fx, fy) to the target, labelled at its start. */
  s.arrowTo = (id, from, o = {}) => add(id, "arrowTo", { fx: from[0], fy: from[1], x: 960, y: 540, color: "accent", label: "", ...o }, o.dur ?? 900);
}
