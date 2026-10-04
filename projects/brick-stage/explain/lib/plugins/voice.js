// Spoken narration: plays the clips embedded by voice.build.mjs at their
// timeline times, and a four-chord music bed that ducks under the voice.
// Both run through the core's renderAudio, so the live page (Sound on) and
// render.mjs's MP4 get the same mix, sample for sample.
(function () {
  if (!window.VOICE_CLIPS) return;
  const BUF = {};
  // decode every clip before the page starts
  BP.ready.push(async () => {
    const ctx = new OfflineAudioContext(1, 1, 48000);
    await Promise.all(Object.entries(window.VOICE_CLIPS).map(async ([key, b64]) => {
      const bin = atob(b64), bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      BUF[key] = await ctx.decodeAudioData(bytes.buffer);
    }));
  });

  // a clip; `at` < 0 means the line started before this render range
  BP.voice("clip", (s, e, at, ctx, out) => {
    const b = BUF[e.clip];
    if (!b) return;
    const src = ctx.createBufferSource(), g = ctx.createGain();
    src.buffer = b; g.gain.value = e.gain ?? 1;
    src.connect(g).connect(out);
    if (at >= 0) src.start(at);
    else if (-at < b.duration) src.start(0, -at);
  });

  // effects dip under the voice too (the core's fx bus)
  BP.audioHooks.push((ctx, { fx }, fromMs) => {
    const off = fromMs / 1000, end = ctx.length / ctx.sampleRate;
    for (const c of BP.TL.sounds) {
      if (c.kind !== "clip") continue;
      const a = c.t / 1000 - off, b = (c.t + c.long) / 1000 - off;
      if (b < 0 || a > end) continue;
      fx.gain.setTargetAtTime(0.5, Math.max(0, a - 0.15), 0.08);
      fx.gain.setTargetAtTime(1, Math.max(0, b + 0.1), 0.25);
    }
  });
  // the music bed: slow chords, ducked about 8 dB while anyone is speaking
  const CHORDS = [[110, 164.81, 220, 261.63], [87.31, 130.81, 174.61, 220], [130.81, 196, 261.63, 329.63], [98, 146.83, 196, 246.94]];
  const BAR = 8, DUCK = 0.4;
  BP.voice("bed", (s, e, at, ctx, out) => {
    const off = -at;                           // timeline seconds at ctx time 0
    const end = ctx.length / ctx.sampleRate;   // ctx seconds available
    const bus = ctx.createGain();
    bus.gain.setValueAtTime(1, 0);
    bus.connect(out);
    // duck under every clip that overlaps this range
    for (const c of BP.TL.sounds) {
      if (c.kind !== "clip") continue;
      const a = c.t / 1000 - off, b = (c.t + c.long) / 1000 - off;
      if (b < 0 || a > end) continue;
      bus.gain.setTargetAtTime(DUCK, Math.max(0, a - 0.15), 0.08);
      bus.gain.setTargetAtTime(1, Math.max(0, b + 0.1), 0.25);
    }
    const pad = (start, f, dur, gain) => {
      for (const [type, det] of [["sine", 0], ["triangle", 6], ["sine", -5]]) {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.type = type; o.frequency.value = f; o.detune.value = det;
        const t0 = Math.max(0, start), into = t0 - start; // already this far into the bar
        g.gain.setValueAtTime(into > 1.6 ? gain : 0.0001, t0);
        if (into < 1.6) g.gain.exponentialRampToValueAtTime(gain, start + 1.6);
        if (start + dur - 1.6 > t0) g.gain.setValueAtTime(gain, start + dur - 1.6);
        g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
        o.connect(g).connect(bus); o.start(t0); o.stop(start + dur + 0.05);
      }
    };
    for (let b = Math.max(0, Math.floor(off / BAR) - 1); b * BAR - off < end; b++) {
      const start = b * BAR - off, ch = CHORDS[b % CHORDS.length];
      if (start + BAR + 1.5 < 0) continue;
      for (const f of ch) pad(start, f, BAR + 1.5, 0.009);
      pad(start, ch[0] / 2, BAR, 0.02);
    }
  });
})();
