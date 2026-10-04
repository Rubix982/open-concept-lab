# Spoken narration

A script can speak its lines. The scene is paced by the real clips: a caption
lasts exactly as long as its voice (plus a short breath), so nothing has to be
timed by hand.

```js
// every narrate() is spoken, by macOS's built-in `say`
export default explainer({ title: "…", voice: { name: "Samantha", rate: 185 } }, (s) => {
  s.narrate("Each column is one layer of GPT-2.");          // spoken, paced by the clip
  s.narrate("A caption only.", { silent: true });          // not spoken
  s.voice("A recorded take.", { file: "takes/line3.wav" }); // your own recording
  s.together((g) => {
    g.bricks("cols", chart);
    g.narrate("Spoken while the chart builds.");            // groups last as long as the line
  });
});
```

Without `voice` in the explainer's options, `narrate()` stays caption-only and
`s.voice(text)` speaks just that line.

| Option | Meaning |
| ------ | ------- |
| `voice: { name, rate }` | `say` voice (`say -v '?'` lists them) and words per minute |
| `s.voice(text, { file })` | use a recording instead; its length is measured with ffprobe |
| `{ hold: false }` | speak without moving the clock on |
| `{ dur }` | at least this long, even if the clip is shorter |
| `{ pad }` | quiet after the line, ms (default 300) |
| `{ delay }` | start the voice this many ms after the caption |
| `{ silent: true }` | (with `voice` on) a caption without a voice |

## How it works

- **Script time** (`lib/actions/voice.mjs`): each line is synthesised with
  `say`, converted to 48 kHz mono WAV and Opus, and measured. Clips are cached
  in `out/.voice-cache/` by text, voice and rate, so a rebuild only speaks lines
  that changed. A line becomes a caption plus a sound event
  `{ kind: "clip", clip, long }`.
- **Build** (`lib/plugins/voice.build.mjs`): the clips the script used are
  embedded in the page as base64 Opus (about 20 KB a line), so the page plays
  them opened from disk.
- **Playback** (`lib/plugins/voice.js`): clips are decoded before the page
  starts, then scheduled through the core's audio renderer. That one mix serves
  the live page (Sound on) and `render.mjs`'s MP4, sample for sample, including
  a line that started before a `--from` range.
- **Ducking:** with a voice, the music bed moves into the plugin and dips about
  8 dB under every spoken line. Sound effects are not ducked.

## Rough edges

- Requires macOS (`say`), ffmpeg and ffprobe at build time.
- Sound effects stay at full level under speech; only the music ducks.
