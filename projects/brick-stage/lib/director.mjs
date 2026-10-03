// The director: a story file calls these methods in order, and the director
// lays every action onto one timeline. The player then evaluates that
// timeline as a pure function of time, so scrubbing is exact and playback is
// smooth however fast the machine is.
//
// Units: studs across, plates up (a brick is 3 plates). Times in ms.
import { check } from "../../brick-check/lib/check.mjs";
import { footprint, PARTS } from "../../brick-check/lib/parts.mjs";
export { mirror } from "../../brick-check/lib/mirror.mjs";

export const P = (part, color, x, y, z, rot = 0) => ({ part, color, x, y, z, rot });

// A model is a list of parts in build order. That order is what the camera
// sees, and brick-check verifies it can really be built that way.
//
// Joints let a character move part of itself: name a group of part indices,
// a pivot [x, y, z] (studs, plates, studs) and an axis ("x" swings forward
// and back, "z" sideways, "y" twists). The model is checked in its rest pose;
// a joint is only physically real if the build uses a hinge there.
// Steps group parts the way an instruction booklet does. By default a new
// step starts at a new layer once the step has 3 parts, or after 10 parts
// (so a model built back and forth between layers doesn't become a booklet of
// one-plate steps); pass `steps: [3, 5, …]` (parts per step) to choose.
export { autoSteps };
export function model(name, parts, { joints = {}, steps } = {}) {
  for (const [j, spec] of Object.entries(joints)) {
    if (!spec.parts?.length || !spec.pivot) throw new Error(`joint "${j}" of "${name}" needs parts and a pivot`);
    for (const i of spec.parts) if (!parts[i]) throw new Error(`joint "${j}" of "${name}" names part ${i}, which doesn't exist`);
  }
  return { name, parts, joints, steps: steps || autoSteps(parts) };
}
function autoSteps(parts) {
  const out = [];
  let n = 0;
  parts.forEach((p, i) => {
    if (i > 0 && ((p.y !== parts[i - 1].y && n >= 3) || n >= 10)) { out.push(n); n = 0; }
    n++;
  });
  if (n) out.push(n);
  return out;
}

function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

const DIRECTIONS = {
  above: (r) => [(r() - 0.5) * 2, 14 + r() * 6, (r() - 0.5) * 2],
  below: (r) => [(r() - 0.5) * 2, -10, (r() - 0.5) * 2],
  left: (r) => [-18 - r() * 4, 3 + r() * 3, (r() - 0.5) * 3],
  right: (r) => [18 + r() * 4, 3 + r() * 3, (r() - 0.5) * 3],
  front: (r) => [(r() - 0.5) * 3, 3 + r() * 3, 16 + r() * 4],
  back: (r) => [(r() - 0.5) * 3, 3 + r() * 3, -16 - r() * 4],
  everywhere: (r) => {
    const a = r() * Math.PI * 2, up = 0.25 + r() * 0.75, d = 14 + r() * 6;
    return [Math.cos(a) * d * (1 - up * 0.5), up * d, Math.sin(a) * d * (1 - up * 0.5)];
  },
};

// The light, for a colour script: from morning to night.
export const MOODS = ["day", "morning", "midday", "overcast", "sunset", "amber", "dusk", "night"];

export const SFX = ["creak", "tik", "knock", "click", "yip", "pop", "cheer", "splash", "whoosh", "switch"];

export class Director {
  constructor(meta) {
    this.meta = meta;
    this.t = 0;
    this.actors = {};      // id -> { model, parts: [...], moves: [...] }
    this.camera = [];      // { t, dur, shot }
    this.captions = [];    // { t, kicker, text }
    this.cards = [];       // { t, dur, kicker, title, sub }
    this.callouts = [];    // { t, dur, text, on, at, offset }
    this.bubbles = [];     // { t, dur, actor, text }
    this.emitters = [];    // { t, dur, kind, on, at, offset, count, seed }
    this.moods = [];       // { t, dur, name }
    this.letterboxes = []; // { t, on, dur }
    this.fades = [];       // { t, on, dur, color }
    this.musicCues = [];   // { t, name }
    this.narration = [];   // { t, dur, text }
    this.sfxCues = [];     // { t, name, gain }
    this.ambienceCues = []; // { t, name }
    this.lights = {};      // id -> { kind, keys: [{ t, dur, ...settings }] }
    this.models = {};
    this.props = {};       // buttons, doors, signal lines
    this.roomSpec = null;
    this._group = null;
    this._seed = 1;
  }
  _advance(end) {
    if (this._group) this._group.end = Math.max(this._group.end, end);
    else this.t = end;
  }

  // A full-screen card. Advances time.
  card(kicker, title, { sub = "", dur = 2800 } = {}) {
    this.cards.push({ t: this.t, dur, kicker, title, sub });
    this._advance(this.t + dur);
    return this;
  }
  // A caption that stays until the next one. Doesn't advance time.
  caption(text, kicker = "") { this.captions.push({ t: this.t, kicker, text }); return this; }
  clearCaption() { return this.caption("", ""); }
  // Ease the camera to a shot. Doesn't advance time.
  // shot: { at: [x, y, z] in studs, az, el (degrees), dist (studs) }
  shot(shot, dur = 1600) { this.camera.push({ t: this.t, dur, shot }); this._lastShot = shot; return this; }
  // Keep the camera on an actor as it moves. Doesn't advance time.
  follow(actor, { az, el, dist, offset, dur = 1400 } = {}) {
    const last = this._lastShot || { az: 20, el: 18, dist: 30 };
    return this.shot({ follow: actor, offset, az: az ?? last.az, el: el ?? last.el, dist: dist ?? last.dist }, dur);
  }
  // Swing the camera around the current target by `deg`. Doesn't advance time.
  orbit(deg, { dur = 3000, el, dist } = {}) {
    const last = this._lastShot;
    if (!last) throw new Error("orbit() needs a shot() or follow() before it");
    return this.shot({ ...last, az: last.az + deg, el: el ?? last.el, dist: dist ?? last.dist }, dur);
  }
  // Make an actor glow, to draw the eye. Doesn't advance time.
  highlight(actor, { dur = 1600, color = "#ff8a2a" } = {}) {
    const a = this.actors[actor];
    if (!a) throw new Error(`no actor "${actor}"`);
    (a.highlights ||= []).push({ t: this.t, dur, color });
    return this;
  }
  // A label with a leader line, pinned to an actor (on) or a point (at).
  // Doesn't advance time.
  callout(text, { on, at, offset = [0, 0, 0], dur = 2600 } = {}) {
    if (on && !this.actors[on]) throw new Error(`no actor "${on}"`);
    if (!on && !at) throw new Error("callout() needs `on` or `at`");
    this.callouts.push({ t: this.t, dur, text, on, at, offset });
    return this;
  }
  wait(ms) { this._advance(this.t + ms); return this; }

  // Assemble a model at a position, piece by piece. Advances time.
  // With `onto`, the parts are added to an actor that is already built (same
  // coordinates, moves with it), and the combined model is what gets checked.
  build(m, { as = m.name, at = [0, 0, 0], from = "everywhere", stagger = 130, dur = 750, seed, onto } = {}) {
    const host = onto && this.actors[onto];
    if (onto && !host) throw new Error(`no actor "${onto}" to build onto`);
    if (!onto && this.actors[as]) throw new Error(`an actor called "${as}" already exists`);
    const checkedAs = host ? `${host.checkedAs} + ${m.name}` : m.name;
    const allParts = host ? [...host.modelParts, ...m.parts] : m.parts;
    if (host) delete this.models[host.checkedAs];
    this.models[checkedAs] = { name: checkedAs, parts: allParts };
    const r = rng(seed ?? this._seed++ * 7919);
    // "path": each part arrives along the way brick-check says it really goes
    // in — straight down, up from below, or slid in from the side.
    let via = null;
    if (from === "path") {
      const res = check({ steps: [{ note: m.name, parts: allParts }] });
      via = res.parts.slice(allParts.length - m.parts.length).map((p) => p.via || "down");
    } else if (!DIRECTIONS[from]) throw new Error(`unknown direction "${from}"`);
    const VIA = { down: [0, 1, 0], up: [0, -1, 0], "slide+x": [1, 0.15, 0], "slide-x": [-1, 0.15, 0], "slide+z": [0, 0.15, -1], "slide-z": [0, 0.15, 1] };
    const parts = m.parts.map((p, i) => {
      const f = footprint(p);
      const d = via ? VIA[via[i]].map((v) => v * (via[i].startsWith("slide") ? 9 : 12)) : DIRECTIONS[from](r);
      return {
        ...p, ...f, kind: PARTS[p.part].kind, mesh: !!PARTS[p.part].mesh, via: via?.[i],
        t0: this.t + i * stagger, dur,
        from: d, spin: via ? [0, 0, 0] : [(r() - 0.5) * 6, (r() - 0.5) * 8, (r() - 0.5) * 6],
      };
    });
    const shift = host ? host.parts.length : 0;
    let k = 0;
    (m.steps || [m.parts.length]).forEach((n) => { if (parts[k]) parts[k].stepStart = true; k += n; });
    const joints = Object.fromEntries(Object.entries(m.joints || {}).map(([j, spec]) => [j, { ...spec, parts: spec.parts.map((i) => i + shift) }]));
    if (host) { host.parts.push(...parts); host.modelParts = allParts; host.checkedAs = checkedAs; Object.assign(host.joints, joints); }
    else this.actors[as] = { model: m.name, checkedAs, modelParts: allParts, parts, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [], joints, poses: [] };
    this._advance(this.t + (m.parts.length - 1) * stagger + dur);
    return this;
  }

  // Walk (or glide) an actor to a new position. Advances time.
  // `arc`: a throw's height in plates; `spin`: degrees turned on the way
  // [x, y, z], for tumbles.
  move(as, to, { dur = 1800, hop, steps, arc = 0, spin } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    if (a.kind === "figure" || a.kind === "minifig") { hop ??= a.kind === "minifig" ? 0.15 : 0.25; steps ??= Math.max(2, Math.round(dur / 330)); }
    hop ??= arc || spin ? 0 : 0.6;
    a.moves.push({ t: this.t, dur, to, hop, steps: steps ?? Math.max(2, Math.round(dur / 300)), arc, spin: spin || null });
    this._advance(this.t + dur);
    return this;
  }

  // Swing a named joint to an angle (degrees, absolute: 0 is the rest pose).
  // Advances time.
  pose(as, joint, deg, { dur = 600 } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    if (!a.joints?.[joint]) throw new Error(`"${as}" has no joint "${joint}"`);
    a.poses.push({ t: this.t, dur, joint, deg });
    this._advance(this.t + dur);
    return this;
  }

  // A line of narration: shown as a subtitle, written to the render's .srt,
  // and your voiceover script. By default the story waits long enough to say
  // it (about 2.6 words a second); pass `wait: false` to keep going under it.
  narrate(text, { dur, wait = true } = {}) {
    dur ??= Math.round(600 + (text.trim().split(/\s+/).length / 2.6) * 1000);
    this.narration.push({ t: this.t, dur, text });
    if (wait) this._advance(this.t + dur);
    return this;
  }

  // A speech bubble over an actor. Advances time while it's on screen.
  say(as, text, { dur = 2400 } = {}) {
    if (!this.actors[as]) throw new Error(`no actor "${as}"`);
    this.bubbles.push({ t: this.t, dur, actor: as, text });
    this._advance(this.t + dur);
    return this;
  }
  // Particles rising from an actor or a point: "hearts", "sparkles" or
  // "confetti". Doesn't advance time.
  emit(kind, { on, at, offset = [0, 0, 0], count = 14, dur = 2600 } = {}) {
    if (!["hearts", "sparkles", "confetti"].includes(kind)) throw new Error(`unknown particles "${kind}"`);
    if (on && !this.actors[on]) throw new Error(`no actor "${on}"`);
    this.emitters.push({ t: this.t, dur, kind, on, at, offset, count, seed: this.emitters.length * 977 + 13 });
    return this;
  }
  // Ease the light to a mood. Doesn't advance time.
  mood(name, { dur = 2500 } = {}) {
    if (!MOODS.includes(name)) throw new Error(`unknown mood "${name}" (try ${MOODS.join(", ")})`);
    this.moods.push({ t: this.t, dur, name });
    return this;
  }
  // Cinema bars top and bottom. Doesn't advance time.
  letterbox(on = true, { dur = 900 } = {}) { this.letterboxes.push({ t: this.t, on, dur }); return this; }
  // Fade the picture out to a colour, or back in. Advances time.
  fadeOut({ dur = 1200, color = "#000" } = {}) { this.fades.push({ t: this.t, on: true, dur, color }); this._advance(this.t + dur); return this; }
  fadeIn({ dur = 1200 } = {}) { this.fades.push({ t: this.t, on: false, dur }); this._advance(this.t + dur); return this; }
  // ---- lights -----------------------------------------------------------
  // A light as an actor. kind: "spot" (a cone, with a visible beam unless
  // beam: false), "point" (a glow), or "patch" (a pool of sunlight on the
  // floor, size [w, d] in studs). Positions are [x, y, z] in studs, plates,
  // studs. A spot aims at `target`, or swings round by `az` degrees (with
  // `reach` studs and `drop` plates down): that's how a lighthouse beam sweeps.
  // Doesn't advance time.
  light(id, { kind = "spot", at = [0, 20, 0], target, color = "#fff2d8", intensity = 1, angle = 25, az, reach = 30, drop = 10, size = [10, 6], beam = true, shadows = true } = {}) {
    if (this.lights[id]) throw new Error(`a light called "${id}" already exists`);
    if (!["spot", "point", "patch"].includes(kind)) throw new Error(`unknown light kind "${kind}"`);
    this.lights[id] = { kind, beam, shadows, keys: [{ t: this.t, dur: 0, at, target, color, intensity, angle, az, reach, drop, size }] };
    return this;
  }
  // Ease a light to new settings (any of the ones light() takes). Advances
  // time by `dur` only with wait: true.
  lightTo(id, settings, { dur = 1500, wait = false } = {}) {
    const L = this.lights[id];
    if (!L) throw new Error(`no light "${id}"`);
    L.keys.push({ t: this.t, dur, ...settings });
    if (wait) this._advance(this.t + dur);
    return this;
  }
  // Switch a model's light on or off: it glows in `color` and lights what's
  // around it (a lighthouse dome, a lamp). Doesn't advance time.
  lamp(actor, on = true, { color = "#ffd36b", intensity = 1, dur = 400 } = {}) {
    const a = this.actors[actor];
    if (!a) throw new Error(`no actor "${actor}"`);
    (a.lamps ||= []).push({ t: this.t, on, dur, color, intensity });
    return this;
  }

  // A sound effect on cue: "creak", "tik", "knock", "click", "yip", "pop",
  // "cheer", "splash", "whoosh", "switch". Doesn't advance time.
  sfx(name, { gain = 1 } = {}) {
    if (!SFX.includes(name)) throw new Error(`unknown sound "${name}" (try ${SFX.join(", ")})`);
    this.sfxCues.push({ t: this.t, name, gain });
    return this;
  }
  // A background bed: "room" (a quiet hum with a ticking clock), or null to
  // stop. Doesn't advance time.
  ambience(name) {
    if (name && name !== "room") throw new Error(`unknown ambience "${name}"`);
    this.ambienceCues.push({ t: this.t, name });
    return this;
  }
  // A soft generated chord pad ("romance", "wonder"), or null to stop it.
  // Doesn't advance time.
  music(name) {
    if (name && !["romance", "wonder"].includes(name)) throw new Error(`unknown music "${name}"`);
    this.musicCues.push({ t: this.t, name });
    return this;
  }

  // Turn an actor in place by `deg` degrees, relative to where it faces now.
  // Positive turns its front toward +x (stage right from the default view).
  // Advances time.
  turn(as, deg, { dur = 700 } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    a.turns.push({ t: this.t, dur, deg });
    this._advance(this.t + dur);
    return this;
  }

  // Throw an actor's pieces away again, last piece first. Advances time.
  unbuild(as, { to = "everywhere", stagger = 60, dur = 650, seed } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    const r = rng(seed ?? this._seed++ * 104729);
    const n = a.parts.length;
    a.parts.forEach((p, i) => { p.out = { t0: this.t + (n - 1 - i) * stagger, dur, to: DIRECTIONS[to](r) }; });
    this._advance(this.t + (n - 1) * stagger + dur);
    return this;
  }

  // ---- set pieces ------------------------------------------------------
  // A tiled room: floor panels flip into place in a wave, then the back and
  // right walls rise. Sizes in studs (w across, d deep) and plates (h up).
  room({ w = 48, d = 36, h = 30, cell = 4, dur = 7000, seed = 5 } = {}) {
    this.roomSpec = { w, d, h, cell, seed, t0: this.t, dur };
    this._advance(this.t + dur);
    return this;
  }
  // A pictogram figure that walks with move(), faces where it's going, and
  // turns with turn(). It drops into place when it appears.
  figure(id, at, { face = 0, dur = 700 } = {}) {
    if (this.actors[id]) throw new Error(`an actor called "${id}" already exists`);
    this.actors[id] = { kind: "figure", t0: this.t, appear: dur, face, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [] };
    this._advance(this.t + dur);
    return this;
  }
  // A minifigure-style character (a rigged figure, not checked LEGO).
  // look: { torso, legs, print, hat, hatColor, hatTilt, beard, face, extra }
  // Joints for pose(): head (turns), arm-l, arm-r (swing forward), hand-l,
  // hand-r (twist), leg-l, leg-r (swing forward), lean (the body tips forward).
  minifig(id, at, { look = {}, facing = 0, dur = 700 } = {}) {
    if (this.actors[id]) throw new Error(`an actor called "${id}" already exists`);
    const joints = Object.fromEntries(["head", "arm-l", "arm-r", "hand-l", "hand-r", "leg-l", "leg-r", "lean"].map((j) => [j, {}]));
    this.actors[id] = { kind: "minifig", t0: this.t, appear: dur, face: facing, look, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [], poses: [], joints, faces: [{ t: -1, expr: look.face || "smile" }] };
    this._advance(this.t + dur);
    return this;
  }
  // Change a minifig's expression. Doesn't advance time.
  face(id, expr) {
    const a = this.actors[id];
    if (a?.kind !== "minifig") throw new Error(`"${id}" isn't a minifig`);
    a.faces.push({ t: this.t, expr });
    return this;
  }
  // Put a prop (any brick actor) in a minifig's hand ("l" or "r"); it rides
  // there, moving with the arm, until drop(). offset: studs, plates, studs
  // from the hand. Doesn't advance time.
  // `upright` (default): the prop hangs level, turning only with the figure,
  // like a lantern; false: it tilts with the hand.
  hold(fig, hand, prop, { offset = [0, 0, 0], upright = true } = {}) {
    const f = this.actors[fig], p = this.actors[prop];
    if (f?.kind !== "minifig") throw new Error(`"${fig}" isn't a minifig`);
    if (!p) throw new Error(`no actor "${prop}"`);
    (p.held ||= []).push({ t: this.t, by: fig, hand: hand === "l" ? "l" : "r", offset, upright });
    return this;
  }
  // Let go: the prop flies (or falls) from the hand to `to`, then rests there.
  // Advances time.
  drop(prop, { to, dur = 900, arc = 0, spin } = {}) {
    const p = this.actors[prop];
    if (!p?.held?.length) throw new Error(`"${prop}" isn't being held`);
    if (!to) throw new Error("drop() needs `to`: where the prop ends up");
    p.held.push({ t: this.t, by: null });
    p.moves.push({ t: this.t, dur, to, hop: 0, steps: 1, arc, spin: spin || null, fromHand: true });
    this._advance(this.t + dur);
    return this;
  }

  button(id, at, { dur = 700 } = {}) { return this._prop(id, { kind: "button", at }, dur); }
  // A sliding door in the back wall: x along the wall in studs, sizes in studs and plates.
  door(id, { x, width = 8, height = 20, dur = 900 } = {}) { return this._prop(id, { kind: "door", x, width, height }, dur); }
  // A dotted signal line through points [x, y, z] (studs, plates, studs); it draws itself.
  signal(id, points, { dur = 2200 } = {}) { return this._prop(id, { kind: "signal", points }, dur); }
  _prop(id, spec, dur) {
    if (this.props[id]) throw new Error(`a prop called "${id}" already exists`);
    this.props[id] = { ...spec, t0: this.t, dur, events: [] };
    this._advance(this.t + dur);
    return this;
  }
  // Switch a prop on or off: a button presses, a signal lights, a door opens.
  _set(id, on, dur) {
    const p = this.props[id];
    if (!p) throw new Error(`no prop "${id}"`);
    p.events.push({ t: this.t, on, dur });
    this._advance(this.t + dur);
    return this;
  }
  press(id, { dur = 250 } = {}) { return this._set(id, true, dur); }
  release(id, { dur = 250 } = {}) { return this._set(id, false, dur); }
  activate(id, { dur = 900 } = {}) { return this._set(id, true, dur); }
  deactivate(id, { dur = 500 } = {}) { return this._set(id, false, dur); }
  open(id, { dur = 900 } = {}) { return this._set(id, true, dur); }
  close(id, { dur = 900 } = {}) { return this._set(id, false, dur); }

  // Start a section of the build, like the booklet's numbered sections.
  // Shows as a chapter and a caption kicker. Doesn't advance time.
  section(title) {
    this.sectionCount = (this.sectionCount || 0) + 1;
    this.captions.push({ t: this.t, kicker: `SECTION ${this.sectionCount}`, text: title });
    return this;
  }
  // Fly a finished sub-assembly onto another actor, at `at` in the host's own
  // coordinates. From then on it moves with the host, and the combined model
  // is what gets checked. Advances time.
  attach(sub, { onto, at, dur = 1400, lift = 8 } = {}) {
    const s = this.actors[sub], h = this.actors[onto];
    if (!s || !h) throw new Error(`attach needs two actors ("${sub}" onto "${onto}")`);
    if (s.attached) throw new Error(`"${sub}" is already attached`);
    const hostAt = h.moves[h.moves.length - 1].to, target = [hostAt[0] + at[0], hostAt[1] + at[1], hostAt[2] + at[2]];
    // lift clear of the host's tallest point, move across, set down — a
    // straight line would pass through the host
    const cur = s.moves[s.moves.length - 1].to;
    const hostTop = hostAt[1] + Math.max(...h.modelParts.map((p) => p.y + footprint(p).h));
    const high = Math.max(hostTop, target[1], cur[1]) + lift;
    s.moves.push({ t: this.t, dur: dur * 0.3, to: [cur[0], high, cur[2]], hop: 0, steps: 1 });
    s.moves.push({ t: this.t + dur * 0.3, dur: dur * 0.45, to: [target[0], high, target[2]], hop: 0, steps: 1 });
    s.moves.push({ t: this.t + dur * 0.75, dur: dur * 0.25, to: target, hop: 0, steps: 1 });
    s.attached = { to: onto, t: this.t + dur, offset: at };
    // the sub-assembly is built on its own first, so it must stand on its own
    this.models[`${s.checkedAs} (built on its own)`] = { name: `${s.checkedAs} (built on its own)`, parts: s.modelParts };
    // then host + sub as one model, in the host's coordinates
    const shifted = s.modelParts.map((p) => ({ ...p, x: p.x + at[0], y: p.y + at[1], z: p.z + at[2] }));
    const name = `${h.checkedAs} + ${s.checkedAs}`;
    delete this.models[h.checkedAs]; delete this.models[s.checkedAs];
    h.modelParts = [...h.modelParts, ...shifted]; h.checkedAs = name; s.checkedAs = name;
    this.models[name] = { name, parts: h.modelParts };
    this._advance(this.t + dur);
    return this;
  }
  // Circle the camera once around an actor. Doesn't advance time.
  // `offset` aims above the actor's base (studs, plates, studs), for tall models.
  turnaround(actor, { dur = 6000, el = 14, dist = 30, offset } = {}) {
    const start = this._lastShot?.az ?? 0;
    this.shot({ follow: actor, offset, az: start, el, dist }, 800);
    const t0 = this.t;
    for (let k = 1; k <= 4; k++) this.camera.push({ t: t0 + 800 + ((k - 1) * (dur - 800)) / 4, dur: (dur - 800) / 4, shot: { follow: actor, offset, az: start + 90 * k, el, dist } });
    this._lastShot = { follow: actor, offset, az: start + 360, el, dist };
    return this;
  }

  // Run several actions at the same time; time moves on to the longest.
  together(fn) {
    const outer = this._group, start = this.t;
    this._group = { end: start };
    fn(this);
    const end = this._group.end;
    this._group = outer;
    this.t = start;
    this._advance(end);
    return this;
  }

  compile() {
    const reports = {};
    for (const [name, m] of Object.entries(this.models)) {
      const r = check({ steps: [{ note: name, parts: m.parts }] });
      const actor = Object.keys(this.actors).find((k) => this.actors[k].checkedAs === name && !this.actors[k].attached);
      reports[name] = { ok: r.ok, errors: r.errors, warnings: r.warnings, stats: r.stats, parts: m.parts, actor };
    }
    return {
      meta: this.meta, duration: this.t + 600,
      actors: Object.fromEntries(Object.entries(this.actors).map(([k, a]) => [k, a.kind === "minifig"
        ? { kind: "minifig", t0: a.t0, appear: a.appear, face: a.face, look: a.look, faces: a.faces, moves: a.moves, turns: a.turns, poses: a.poses, joints: a.joints, highlights: a.highlights || [] }
        : a.kind === "figure"
        ? { kind: "figure", t0: a.t0, appear: a.appear, face: a.face, moves: a.moves, turns: a.turns, highlights: a.highlights || [] }
        : { kind: "bricks", parts: a.parts, moves: a.moves, turns: a.turns, highlights: a.highlights || [], joints: a.joints || {}, poses: a.poses || [], attached: a.attached || null, held: a.held || [], lamps: a.lamps || [] }])),
      callouts: this.callouts, bubbles: this.bubbles, emitters: this.emitters, moods: this.moods,
      letterboxes: this.letterboxes, fades: this.fades, music: this.musicCues, narration: this.narration, sfx: this.sfxCues, ambience: this.ambienceCues, lights: this.lights,
      props: this.props, room: this.roomSpec, camera: this.camera, captions: this.captions, cards: this.cards,
      reports,
    };
  }
}

export function story(meta, fn) {
  const d = new Director(meta);
  fn(d);
  return d.compile();
}
