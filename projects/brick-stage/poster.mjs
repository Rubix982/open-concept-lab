#!/usr/bin/env node
// node poster.mjs [story …]  — a still image of each story for gallery cards,
// so a page listing stories doesn't have to run every one of them live.
// Shoots out/<story>/index.html at the story's `meta.poster` moment (ms; by
// default 80% of the way through) and saves out/<story>/poster.jpg.
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
let names = process.argv.slice(2);
if (!names.length) names = (await fs.readdir(path.join(here, "stories"))).filter((f) => f.endsWith(".mjs") && !f.startsWith("_")).map((f) => f.slice(0, -4));

const shells = (await fs.readdir(path.join(os.homedir(), "Library/Caches/ms-playwright")).catch(() => []))
  .filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
  .map((d) => path.join(os.homedir(), "Library/Caches/ms-playwright", d, "chrome-headless-shell-mac-arm64/chrome-headless-shell"));
let chrome = null;
for (const c of [process.env.CHROME, ...shells, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean)) {
  try { await fs.access(c); chrome = c; break; } catch {}
}
if (!chrome) { console.log("no headless Chrome found (set CHROME=/path/to/chrome)"); process.exit(1); }

for (const name of names) {
  const story = (await import(pathToFileURL(path.join(here, "stories", `${name}.mjs`)).href)).default;
  const t = story.meta.poster ?? Math.round(story.duration * 0.8);
  const page = path.join(here, "out", name, "index.html"), png = path.join(os.tmpdir(), `brick-stage-${name}.png`), jpg = path.join(here, "out", name, "poster.jpg");
  execFileSync(chrome, ["--headless", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars", "--window-size=1280,800",
    "--virtual-time-budget=6000", `--screenshot=${png}`, `${pathToFileURL(page).href}?t=${t}&clean`], { stdio: "ignore", timeout: 120000 });
  execFileSync("sips", ["-s", "format", "jpeg", "-s", "formatOptions", "78", png, "--out", jpg], { stdio: "ignore" });
  const kb = Math.round((await fs.stat(jpg)).size / 1024);
  console.log(`${story.meta.title} · ${(t / 1000).toFixed(1)} s → out/${name}/poster.jpg (${kb} KB)`);
}
