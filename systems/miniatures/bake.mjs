#!/usr/bin/env node
// Save each page's runs to site/baked/<name>.js, so the pages also work when
// opened straight from disk (where browsers won't load the WebAssembly).
//
//   node bake.mjs            every page
//   node bake.mjs herd       just one
//
// For each page it serves site/, opens the page in headless Chrome with
// ?bake=1 (mini.js then records every run), waits for the default run, clicks
// every option button in the controls once (returning to the default after
// each), plays a scripted example if the page has one, and writes what was
// recorded. Needs a Chromium: CHROME=/path, or Playwright's headless shell.
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const site = path.join(here, "site");
const PAGES = ["cache-router", "batching", "disagg", "straggler", "double-charge", "herd", "local-first"];
const only = process.argv.slice(2);

// ---- a tiny static server for site/
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".wasm": "application/wasm", ".json": "application/json", ".jpg": "image/jpeg" };
const server = http.createServer(async (req, res) => {
  const file = path.join(site, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!file.startsWith(site)) { res.writeHead(403).end(); return; }
  try {
    const body = await fs.readFile(file);
    res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream" }).end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}`;

// ---- headless Chrome over the DevTools protocol
async function findChrome() {
  const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
  const dirs = await fs.readdir(cache).catch(() => []);
  const shells = dirs.filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
    .map((d) => path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell"));
  for (const c of [process.env.CHROME, ...shells, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean)) {
    try { await fs.access(c); return c; } catch {}
  }
  throw new Error("no Chromium found; set CHROME=/path/to/chrome");
}
const port = 9500 + Math.floor(Math.random() * 400);
const profile = await fs.mkdtemp(path.join(os.tmpdir(), "bake-"));
const chrome = spawn(await findChrome(), ["--headless", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--window-size=1280,900", "about:blank"], { stdio: "ignore" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let tabs;
for (let i = 0; i < 50 && !tabs; i++) { await wait(200); tabs = await fetch(`http://127.0.0.1:${port}/json`).then((r) => r.json()).catch(() => null); }
const ws = new WebSocket(tabs.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = {};
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (pending[d.id]) { pending[d.id](d); delete pending[d.id]; } };
const send = (method, params = {}) => new Promise((r) => { pending[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression) => {
  const d = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (d.result?.exceptionDetails) throw new Error(d.result.exceptionDetails.exception?.description || "page error");
  return d.result?.result?.value;
};

// clicks every option button in the controls once, back to the default after each
const CLICK_THROUGH = `(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (const seg of document.querySelectorAll(".controls .seg, .panel .seg:not(.player .seg)")) {
    if (seg.closest(".player")) continue;
    const buttons = [...seg.querySelectorAll("button")];
    const start = buttons.find((b) => b.getAttribute("aria-pressed") === "true");
    for (const b of buttons) {
      if (b === start) continue;
      b.click(); await sleep(900);
      if (start) { start.click(); await sleep(900); }
    }
  }
  const demo = [...document.querySelectorAll("button")].find((b) => /play the example/i.test(b.textContent));
  if (demo) { demo.click(); await sleep(3000); }
  return true;
})()`;

let failed = 0;
await fs.mkdir(path.join(site, "baked"), { recursive: true });
for (const name of PAGES.filter((p) => !only.length || only.includes(p))) {
  await send("Page.navigate", { url: `${base}/${name}.html?bake=1` });
  await wait(3000);
  await evaluate(CLICK_THROUGH);
  await wait(800);
  const table = await evaluate(`JSON.stringify((window.__baked || {})[${JSON.stringify(name)}] || {})`);
  const runs = Object.keys(JSON.parse(table)).length;
  if (!runs) { console.log(`${name}: nothing recorded`); failed++; continue; }
  const js = `// Saved runs for ${name}.html, written by bake.mjs — do not edit.\nMini.bake(${JSON.stringify(name)}, ${table});\n`;
  await fs.writeFile(path.join(site, "baked", `${name}.js`), js);
  console.log(`${name}: ${runs} runs, ${(js.length / 1024).toFixed(0)} KB`);
}

ws.close();
chrome.kill();
server.close();
await fs.rm(profile, { recursive: true, force: true });
process.exit(failed ? 1 : 0);
