// Build hook for spoken narration: embeds every clip the script used (Opus in
// Ogg, base64) so the page plays them from disk, and tidies the build-only
// fields off the timeline.
import fs from "node:fs/promises";

export async function build(tl, { log }) {
  const clips = tl.voiceClips;
  delete tl.voiceClips;
  delete tl._voiceBed;
  if (!clips) return "";
  const out = {};
  let bytes = 0;
  for (const [key, file] of Object.entries(clips)) {
    const b = await fs.readFile(file);
    bytes += b.length;
    out[key] = b.toString("base64");
  }
  const lines = tl.sounds.filter((e) => e.kind === "clip").length;
  log(`🗣 ${lines} spoken lines · ${Object.keys(out).length} clips · ${(bytes / 1024).toFixed(0)} KB`);
  return `<script>window.VOICE_CLIPS = ${JSON.stringify(out)};</script>`;
}
