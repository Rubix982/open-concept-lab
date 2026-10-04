// The explainer script language: a scene is written as a sequence of actions
// on a clock, and compiles to a timeline the blueprint player draws as a pure
// function of time (so render.mjs can photograph any frame exactly).
//
//   export default explainer({ title: "…" }, (s) => {
//     s.heading("where a model keeps a fact");
//     s.tokens("prompt", ["The", " E", "iff"], { x: 960, y: 540 });
//     s.narrate("GPT-2 finishes this sentence with Paris.");
//     s.together((g) => { g.set("prompt", { y: 300 }); g.dial(1, "logit lens"); });
//   });
//
// Every action starts at the clock's current time and moves it on by its
// duration, except inside together(), where actions start at the same time
// and the clock moves on by the longest. Positions are in a 1920×1080 frame.

const WPM = 175; // narration reading pace

export function explainer(meta, write) {
  const tl = { meta: { w: 1920, h: 1080, ...meta }, objects: [], tweens: [], sounds: [], narration: [] };
  const ids = new Set();
  let order = 0;

  // A clock. In a group (together), actions all start at the group's start
  // and the group remembers the longest; otherwise each action moves time on.
  function clock(start, group = false) {
    const s = { t: start, _max: start };
    const span = (dur) => {
      const t0 = s.t;
      if (group) s._max = Math.max(s._max, t0 + dur);
      else s.t += dur;
      return t0;
    };

    // ---- objects
    const add = (id, type, props, reveal = 600) => {
      if (ids.has(id)) throw new Error(`explain: "${id}" already exists`);
      ids.add(id);
      tl.objects.push({ id, type, born: s.t, order: order++, props: { opacity: 1, reveal: 0, ...props } });
      const t0 = span(reveal);
      tl.tweens.push({ id, prop: "reveal", to: 1, t0, t1: t0 + Math.max(1, reveal), ease: "out" });
      return s;
    };
    const need = (id) => { if (!ids.has(id)) throw new Error(`explain: no object "${id}"`); };

    /** The chapter title, top left, underlined as it writes. */
    s.heading = (text, o = {}) => {
      const id = o.id || `heading-${order}`;
      if (s._heading) { need(s._heading); tl.tweens.push({ id: s._heading, prop: "opacity", to: 0, t0: s.t, t1: s.t + 300, ease: "inout" }); }
      s._heading = id;
      return add(id, "heading", { text, x: o.x ?? 96, y: o.y ?? 92 }, o.dur ?? 700);
    };
    /** Text that types itself on. font: "mono" | "sans". */
    s.text = (id, text, o = {}) => add(id, "text", { text, x: 960, y: 540, size: 32, font: "sans", color: "ink", align: "center", weight: 500, ...o }, o.dur ?? Math.min(1400, 40 * text.length));
    /** A row of token chips. hl: indices drawn in the accent; noise: 0..1 scrambles the hl chips. */
    s.tokens = (id, list, o = {}) => add(id, "tokens", { list, x: 960, y: 540, size: 34, hl: [], noise: 0, gap: 10, ...o }, o.dur ?? 90 * list.length);
    /** A labelled chip, e.g. the model's answer. */
    s.chip = (id, label, o = {}) => add(id, "chip", { label, value: o.value ?? null, x: 960, y: 540, size: 34, accent: true, ...o }, o.dur ?? 500);
    /** A grid of nodes: columns are words, rows are layers. */
    s.lattice = (id, o) => add(id, "lattice", { cols: 11, rows: 25, x: 600, y: 180, w: 900, h: 640, hiCol: -1, flow: 0, labels: null, labelUpTo: -1, ...o }, o.dur ?? 1600);
    /** A heat map; values[row][col] in 0..1, revealed column by column. */
    s.heat = (id, o) => add(id, "heat", { x: 600, y: 200, cell: 20, values: [[0]], rowLabels: [], colLabels: [], hue: "accent", title: "", ...o }, o.dur ?? 2400);
    /** A line chart that draws itself. points: [[x, y]], logY optional. */
    s.chart = (id, o) => add(id, "chart", { x: 1250, y: 300, w: 560, h: 340, points: [], xMax: 1, yMin: 0, yMax: 1, logY: false, xTicks: [], yTicks: [], title: "", marks: [], ...o }, o.dur ?? 2200);
    /** The side list (like a display list); `active` moves the pointer. */
    s.list = (id, items, o = {}) => add(id, "list", { items, x: 96, y: 260, gap: 46, active: -1, title: "", ...o }, o.dur ?? 140 * items.length);
    /** The step dial, top right. Call again to advance it. */
    s.dial = (n, label, o = {}) => {
      if (!ids.has("dial")) add("dial", "dial", { n, label, of: o.of ?? 4, x: 1780, y: 110, spin: 0 }, 500);
      else {
        tl.tweens.push({ id: "dial", prop: "n", to: n, t0: s.t, t1: s.t + 500, ease: "inout" });
        tl.tweens.push({ id: "dial", prop: "label", to: label, t0: s.t, t1: s.t + 1, ease: "step" });
        s.sfx("tick");
      }
      return s;
    };
    /** A path through points that draws on; pulses travel along it. */
    s.path = (id, pts, o = {}) => add(id, "path", { pts, curve: true, pulses: 0, period: 1600, color: "ink", width: 2, arrow: true, ...o }, o.dur ?? 900);
    /** A 3D stage: a stack of layer plates (rows) with a node per word (cols),
     *  seen by an orbiting camera (az, el, dist — tween them with set). */
    s.stage3d = (id, o) => add(id, "stage3d", { x: 0, y: 0, w: 1920, h: 1080, rows: 25, cols: 11, az: 30, el: 18, dist: 24, hiCol: -1, scan: -1, labels: null, labelUpTo: -1, glow: [], route: null, routeK: 0, colLabels: null, ...o }, o.dur ?? 2400);
    /** A box with a label in its corner. */
    s.box = (id, o) => add(id, "box", { x: 0, y: 0, w: 200, h: 100, label: "", color: "ink", dash: false, ...o }, o.dur ?? 700);
    /** A small note with a leader line to a point. */
    s.note = (id, text, o) => add(id, "note", { text, x: 0, y: 0, to: null, align: "left", size: 24, color: "accent", ...o }, o.dur ?? 700);

    // ---- changes
    /** Tween any numeric props (strings switch at the start). */
    s.set = (id, props, o = {}) => {
      need(id);
      const dur = o.dur ?? 700, t0 = span(dur);
      for (const [prop, to] of Object.entries(props)) {
        tl.tweens.push({ id, prop, to, t0, t1: t0 + Math.max(1, dur), ease: typeof to === "number" ? o.ease || "inout" : "step" });
      }
      return s;
    };
    s.fade = (id, to = 0, o = {}) => s.set(id, { opacity: to }, { dur: o.dur ?? 500 });
    /** Fade out everything listed, together. */
    s.clear = (list, o = {}) => s.together((g) => list.forEach((id) => g.fade(id, 0, o)));

    // ---- time, words, sound
    s.wait = (ms) => { span(ms); return s; };
    s.together = (fn) => {
      const g = clock(s.t, true);
      g._heading = s._heading;
      fn(g);
      s._heading = g._heading;
      span(g._max - s.t);
      return s;
    };
    /** A sequence that starts ms from now — inside together(), for actions
     *  that should follow each other while the rest of the group runs. */
    s.after = (ms, fn) => {
      const g = clock(s.t + ms);
      g._heading = s._heading;
      fn(g);
      s._heading = g._heading;
      span(g.t - s.t);
      return s;
    };
    /** A caption line; the clock waits for it to be read (or for dur). */
    s.narrate = (text, o = {}) => {
      const words = text.split(/\s+/).length;
      const dur = o.dur ?? Math.max(1800, (words / WPM) * 60000 + 600);
      tl.narration.push({ t: s.t, dur, text });
      if (o.hold !== false) span(dur);
      return s;
    };
    /** A sound cue: tick, draw, chime, glitch, whoosh, thud, rise. */
    s.sfx = (kind, o = {}) => { tl.sounds.push({ t: s.t, kind, ...o }); return s; };
    return s;
  }

  const root = clock(0);
  write(root);

  tl.meta.duration = Math.ceil(Math.max(root.t, ...tl.narration.map((n) => n.t + n.dur), ...tl.tweens.map((x) => x.t1)) + 600);
  tl.objects.sort((a, b) => a.order - b.order);
  return tl;
}
