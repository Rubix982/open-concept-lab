// Spoken narration. s.voice(text) speaks a line (macOS `say`, or a recorded
// file) and paces the scene by the real clip: the caption lasts as long as the
// voice. With explainer({ voice: { name, rate } }) every s.narrate() is spoken.
//
//   s.voice("Each word becomes a column of numbers.");
//   s.voice("Recorded take.", { file: "takes/line3.wav" });
//   s.voice("…", { hold: false });        // speak while the clock runs on (in groups)
//
// Clips are cached under out/.voice-cache/ by (text, voice, rate), so a rebuild
// only synthesises lines that changed. The build hook (plugins/voice.build.mjs)
// embeds them in the page; plugins/voice.js plays them, live and in render.mjs,
// and ducks the music bed under the voice.
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const CACHE = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "out", ".voice-cache");
const DEFAULTS = { engine: "say", name: "Samantha", rate: 185 };
const PAD = 300; // ms of quiet after each line before the next

function seconds(file) {
  return +execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file], { encoding: "utf8" }).trim();
}

/** A clip for this line: { key, ogg, ms }. Synthesised (or converted) once, then cached. */
export function clip(text, o = {}) {
  fs.mkdirSync(CACHE, { recursive: true });
  const v = { ...DEFAULTS, ...o };
  const src = o.file ? path.resolve(o.file) : null;
  const key = crypto.createHash("sha1").update(JSON.stringify(src ? { file: src, mtime: fs.statSync(src).mtimeMs } : { text, name: v.name, rate: v.rate })).digest("hex").slice(0, 16);
  const wav = path.join(CACHE, `${key}.wav`), ogg = path.join(CACHE, `${key}.ogg`);
  if (!fs.existsSync(ogg) || !fs.existsSync(wav)) {
    let input = src;
    if (!input) {
      input = path.join(CACHE, `${key}.aiff`);
      execFileSync("say", ["-v", v.name, "-r", String(v.rate), "-o", input, text]);
    }
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", input, "-ac", "1", "-ar", "48000", wav]);
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", wav, "-c:a", "libopus", "-b:a", "40k", ogg]);
    if (!src) fs.rmSync(input, { force: true });
  }
  return { key, ogg, ms: Math.round(seconds(wav) * 1000) };
}

export function install(s, { span, tl }) {
  const voiced = tl.meta.voice ? { ...DEFAULTS, ...(tl.meta.voice === true ? {} : tl.meta.voice) } : null;
  // the music bed moves into the plugin, so it can duck under the voice
  const bed = () => {
    if (tl._voiceBed || tl.meta.music === false) return;
    tl._voiceBed = true;
    tl.meta.music = false;
    tl.sounds.push({ t: 0, kind: "bed", long: 1e9 });
  };

  s.voice = (text, o = {}) => {
    const c = clip(text, { ...(voiced || {}), ...o });
    (tl.voiceClips ||= {})[c.key] = c.ogg;
    bed();
    const dur = Math.max(o.dur ?? 0, c.ms + (o.pad ?? PAD));
    tl.sounds.push({ t: s.t + (o.delay ?? 0), kind: "clip", clip: c.key, long: c.ms });
    tl.narration.push({ t: s.t, dur, text });
    if (o.hold !== false) span(dur);
    return s;
  };

  if (voiced) {
    // every narrate() is spoken (an explicit dur still applies if it's longer);
    // narrate(text, { silent: true }) keeps a caption without a voice
    const quiet = s.narrate;
    s.narrate = (text, o = {}) => (o.silent ? quiet(text, o) : s.voice(text, o));
  }
}
