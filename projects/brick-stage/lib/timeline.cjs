// The timeline: everything on stage as a pure function of time. The player
// draws from it, the build uses it to check the stage for collisions, and the
// tests exercise it directly. No three.js in here — positions are in story
// units (studs across, plates up, studs deep).
(function (root) {
  const PLATE = 0.4;
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const easeIn = (p) => p * p;
  const easeInOut = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const settle = (p) => easeOut(p) + Math.sin(p * Math.PI) * 0.06 * (1 - p);
  const lerp = (a, b, p) => a + (b - a) * p;
  const lerpAngle = (a, b, p) => a + ((((b - a + Math.PI * 3) % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2) - Math.PI) * p;

  // Where an actor stands: { x, y, z } in story units, plus lift (plates) from
  // hopping or walking, and the move in progress if any.
  // `actors` lets an attached sub-assembly ride along with its host.
  function actorPos(a, t, actors) {
    if (a.attached && actors && t >= a.attached.t) {
      const h = actors[a.attached.to], hp = actorPos(h, t, actors), hc = actorCentre(h), sc = actorCentre(a);
      const r = (actorTurn(h, t, actors) * Math.PI) / 180, cs = Math.cos(r), sn = Math.sin(r);
      const dx = a.attached.offset[0] + sc[0] - hc[0], dz = a.attached.offset[2] + sc[1] - hc[1];
      return { x: hp.x + hc[0] + dx * cs - dz * sn - sc[0], y: hp.y + a.attached.offset[1], z: hp.z + hc[1] + dx * sn + dz * cs - sc[1], lift: hp.lift, active: null };
    }
    let pos = a.moves[0].to.slice(), lift = 0, active = null;
    for (const m of a.moves.slice(1)) {
      if (t < m.t) break;
      const p = clamp01((t - m.t) / m.dur);
      if (p < 1) {
        const e = m.arc ? p : easeInOut(p);                      // throws travel at an even pace
        lift = Math.abs(Math.sin(p * Math.PI * m.steps)) * m.hop + (m.arc ? 4 * m.arc * p * (1 - p) : 0);
        active = { move: m, p, from: pos.slice() };
        pos = pos.map((v, i) => lerp(v, m.to[i], e));
      } else pos = m.to.slice();
    }
    return { x: pos[0], y: pos[1], z: pos[2], lift, active };
  }

  // Total tumble so far from moves with `spin`, as [x, y, z] degrees.
  function actorSpin(a, t) {
    const out = [0, 0, 0];
    for (const m of a.moves || []) {
      if (!m.spin || t < m.t) continue;
      const p = clamp01((t - m.t) / m.dur);
      for (let i = 0; i < 3; i++) out[i] += m.spin[i] * p;
    }
    return out;
  }
  // A minifig's expression at time t.
  function faceAt(a, t) { let e = "smile"; for (const f of a.faces || []) if (f.t <= t) e = f.expr; return e; }
  // Who holds a prop at time t (null when nobody does).
  function holderAt(a, t) { let h = null; for (const e of a.held || []) if (e.t <= t) h = e.by ? e : null; return h; }

  // Sum of turn() calls so far, in degrees.
  function actorTurn(a, t, actors) {
    let deg = a.attached && actors && t >= a.attached.t ? actorTurn(actors[a.attached.to], t, actors) : 0;
    for (const k of a.turns || []) {
      if (t < k.t) break;
      const p = easeInOut(clamp01((t - k.t) / k.dur));
      deg += k.deg * p;
      if (p < 1) break;
    }
    return deg;
  }

  // Figures face the way they walk (radians, three.js y-rotation), and swing
  // their legs while they do.
  function figurePose(a, t) {
    let heading = ((a.face || 0) * Math.PI) / 180, pos = a.moves[0].to, swing = 0;
    for (const m of a.moves.slice(1)) {
      if (t < m.t) break;
      const dx = m.to[0] - pos[0], dz = m.to[2] - pos[2];
      if (Math.hypot(dx, dz) > 0.01) {
        heading = lerpAngle(heading, Math.atan2(dx, -dz), easeInOut(clamp01((t - m.t) / Math.min(450, m.dur * 0.35))));
        const p = clamp01((t - m.t) / m.dur);
        if (p < 1) swing = Math.sin(p * Math.PI * m.steps) * 0.6 * Math.sin(p * Math.PI);
      }
      pos = m.to;
    }
    return { heading: heading + (actorTurn(a, t) * Math.PI) / 180, swing };
  }

  // A brick part: k is how far it still has to fly in (1 → 0), out how far it
  // has flown away again (0 → 1).
  function partState(p, t) {
    if (t < p.t0) return { visible: false, k: 1, out: 0, settled: false };
    const k = 1 - settle(clamp01((t - p.t0) / p.dur));
    const out = p.out && t >= p.out.t0 ? easeIn(clamp01((t - p.out.t0) / p.out.dur)) : 0;
    return { visible: out < 1, k, out, settled: t >= p.t0 + p.dur && out === 0 };
  }

  // A prop's on/off level (0..1), easing between states.
  function propLevel(p, t) {
    let v = 0;
    for (const e of p.events || []) {
      if (t < e.t) break;
      v += ((e.on ? 1 : 0) - v) * easeInOut(clamp01((t - e.t) / Math.max(1, e.dur)));
    }
    return v;
  }

  // A joint's angle in degrees: each pose() eases from where the joint was.
  function jointAngle(a, joint, t) {
    let deg = 0;
    for (const p of a.poses || []) {
      if (p.joint !== joint || t < p.t) continue;
      deg += (p.deg - deg) * easeInOut(clamp01((t - p.t) / Math.max(1, p.dur)));
    }
    return deg;
  }

  // On/off events (letterbox, fades) as a level 0..1.
  function level(events, t) {
    let v = 0;
    for (const e of events || []) {
      if (t < e.t) break;
      v += ((e.on ? 1 : 0) - v) * easeInOut(clamp01((t - e.t) / Math.max(1, e.dur)));
    }
    return v;
  }

  // The light, as weights over the three moods (they sum to 1).
  function moodWeights(story, t) {
    let w = { day: 1, morning: 0, midday: 0, overcast: 0, sunset: 0, amber: 0, dusk: 0, night: 0 };
    for (const m of story.moods || []) {
      if (t < m.t) break;
      const p = easeInOut(clamp01((t - m.t) / Math.max(1, m.dur)));
      w = Object.fromEntries(Object.entries(w).map(([k, v]) => [k, v * (1 - p) + (k === m.name ? p : 0)]));
    }
    return w;
  }

  // Which bubbles are on screen.
  function bubblesAt(story, t) { return (story.bubbles || []).filter((b) => t >= b.t && t <= b.t + b.dur); }

  // A highlight's glow (0..1): pulses twice over its duration.
  function glow(a, t) {
    let g = 0;
    for (const h of a.highlights || []) {
      if (t < h.t || t > h.t + h.dur) continue;
      const p = (t - h.t) / h.dur;
      g = Math.max(g, Math.sin(p * Math.PI) * (0.6 + 0.4 * Math.cos(p * Math.PI * 4)));
    }
    return g;
  }

  // ---- camera --------------------------------------------------------------
  // A shot looks at a fixed point (`at`) or follows an actor (`follow`), and
  // each keyframe eases from wherever the camera was at that moment.
  function shotTarget(story, shot, t) {
    if (shot.follow) {
      const a = story.actors[shot.follow];
      const p = actorPos(a, t, story.actors), o = shot.offset || [0, 6, 0], c = actorCentre(a);
      return [p.x + c[0] + o[0], p.y + o[1], p.z + c[1] + o[2]];
    }
    return shot.at;
  }
  function actorCentre(a) {
    if (!a.parts || !a.parts.length) return [0, 0];
    const xs = a.parts.flatMap((p) => [p.x, p.x + p.w]), zs = a.parts.flatMap((p) => [p.z, p.z + p.d]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...zs) + Math.max(...zs)) / 2];
  }
  function cameraState(story, t, upto = story.camera.length) {
    const cams = story.camera;
    let i = -1;
    for (let j = 0; j < upto; j++) if (cams[j].t <= t) i = j;
    if (i < 0) i = 0;
    const to = cams[i].shot, at = shotTarget(story, to, t);
    const target = { az: to.az, el: to.el, dist: to.dist, x: at[0], y: at[1], z: at[2] };
    if (i === 0 && cams[0].t >= t) return target;
    const from = i === 0 ? target : cameraState(story, cams[i].t, i);
    const e = easeInOut(clamp01((t - cams[i].t) / Math.max(1, cams[i].dur)));
    const out = {};
    for (const k of Object.keys(target)) out[k] = lerp(from[k], target[k], e);
    return out;
  }

  // ---- chapters and sound ------------------------------------------------
  function chapters(story) {
    return story.captions.filter((c) => c.text).map((c) => ({ t: c.t, label: c.kicker ? `${c.kicker} · ${c.text}` : c.text }));
  }

  // Every sound the story makes, in time order: { t, kind, size }.
  function soundEvents(story) {
    const ev = [];
    for (const a of Object.values(story.actors)) {
      for (const p of a.parts || []) {
        ev.push({ t: p.t0 + p.dur * 0.82, kind: "click", size: p.w * p.d * p.h });
        if (p.out) ev.push({ t: p.out.t0, kind: "whoosh", size: 1 });
      }
      if (a.kind === "figure" || a.kind === "minifig") {
        ev.push({ t: a.t0 + a.appear * 0.7, kind: "thud", size: 1 });
        for (const m of a.moves.slice(1)) for (let s = 1; s <= m.steps; s++) ev.push({ t: m.t + (m.dur * s) / (m.steps + 1), kind: "step", size: 1 });
      }
    }
    for (const p of Object.values(story.props || {})) {
      ev.push({ t: p.t0 + p.dur * 0.6, kind: "install", size: 1 });
      for (const e of p.events) ev.push({ t: e.t, kind: `${p.kind}-${e.on ? "on" : "off"}`, size: 1 });
    }
    for (const b of story.bubbles || []) ev.push({ t: b.t, kind: "say", size: b.text.length });
    for (const e of story.emitters || []) ev.push({ t: e.t, kind: `emit-${e.kind}`, size: e.count });
    // music: one chord per bar while a piece is playing
    const BAR = 2400, music = story.music || [];
    music.forEach((m, i) => {
      if (!m.name) return;
      const end = i + 1 < music.length ? music[i + 1].t : story.duration;
      for (let k = 0, t = m.t; t < end; k++, t += BAR) ev.push({ t, kind: "chord", size: k, piece: m.name });
    });
    if (story.room) {
      const n = 26;      // the floor wave, as a patter rather than one click per panel
      for (let i = 0; i < n; i++) ev.push({ t: story.room.t0 + (story.room.dur * 0.8 * i) / n + 200, kind: "panel", size: 1 });
    }
    return ev.sort((a, b) => a.t - b.t);
  }

  // ---- stage check -------------------------------------------------------
  // Boxes for everything solid on stage at time t (story units), for the
  // collision check. Brick parts count once they have landed.
  function solidBoxes(story, t) {
    const boxes = [];
    for (const [id, a] of Object.entries(story.actors)) {
      const pos = actorPos(a, t, story.actors), y0 = pos.y + pos.lift;
      if (a.kind === "figure" || a.kind === "minifig") {
        if (t < a.t0 + a.appear) continue;
        const [hx, hz, ht] = a.kind === "minifig" ? [0.95, 0.5, 11] : [0.7, 0.7, 14];   // half-width, half-depth, height in plates
        boxes.push({ id, min: [pos.x - hx, y0, pos.z - hz], max: [pos.x + hx, y0 + ht, pos.z + hz] });
        continue;
      }
      if (holderAt(a, t)) continue;
      const deg = actorTurn(a, t, story.actors), c = actorCentre(a), r = (deg * Math.PI) / 180, cs = Math.cos(r), sn = Math.sin(r);
      for (const p of a.parts) {
        if (!partState(p, t).settled) continue;
        const xs = [], zs = [];
        for (const [x, z] of [[p.x, p.z], [p.x + p.w, p.z], [p.x, p.z + p.d], [p.x + p.w, p.z + p.d]]) {
          const dx = x - c[0], dz = z - c[1];
          xs.push(c[0] + dx * cs - dz * sn); zs.push(c[1] + dx * sn + dz * cs);   // same sense as turn() on screen
        }
        boxes.push({ id, min: [pos.x + Math.min(...xs), y0 + p.y, pos.z + Math.min(...zs)], max: [pos.x + Math.max(...xs), y0 + p.y + p.h, pos.z + Math.max(...zs)] });
      }
    }
    return boxes;
  }
  // Moments when two different actors overlap. Reports the first moment of
  // each overlapping pair.
  function stageCollisions(story, { step = 100, slack = 0.15 } = {}) {
    const seen = new Map();
    for (let t = 0; t <= story.duration; t += step) {
      const b = solidBoxes(story, t);
      for (let i = 0; i < b.length; i++) for (let j = i + 1; j < b.length; j++) {
        if (b[i].id === b[j].id) continue;
        const hit = [0, 1, 2].every((q) => b[i].min[q] < b[j].max[q] - slack && b[j].min[q] < b[i].max[q] - slack);
        const key = [b[i].id, b[j].id].sort().join(" & ");
        if (hit && !seen.has(key)) seen.set(key, t);
      }
    }
    return [...seen].map(([pair, t]) => ({ pair, t }));
  }

  const api = { PLATE, clamp01, easeOut, easeIn, easeInOut, settle, actorPos, actorTurn, figurePose, partState, propLevel, glow, actorCentre, cameraState, chapters, soundEvents, solidBoxes, stageCollisions, jointAngle, level, moodWeights, bubblesAt, actorSpin, faceAt, holderAt };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.TL = api;
})(typeof window !== "undefined" ? window : globalThis);
