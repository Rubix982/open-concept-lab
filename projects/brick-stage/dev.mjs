#!/usr/bin/env node
// node dev.mjs [story] [port] — a live preview. Rebuilds whenever a story,
// the player or brick-check changes, and the open page reloads itself at the
// moment you were watching.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2] || "little-builder";
const port = +process.argv[3] || 5173;
const clients = new Set();

// Each rebuild runs in a fresh process so every module is re-read from disk.
let building = false, again = false;
function rebuild() {
  if (building) { again = true; return; }
  building = true;
  const p = spawn(process.execPath, [path.join(here, "build.mjs"), name], { stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  p.stdout.on("data", (d) => (out += d)); p.stderr.on("data", (d) => (out += d));
  p.on("close", () => {
    building = false;
    console.log(`\n[${new Date().toLocaleTimeString()}] rebuilt\n${out.trim()}`);
    for (const res of clients) res.write(`data: reload\n\n`);
    if (again) { again = false; rebuild(); }
  });
}

const RELOAD = `<script>
new EventSource("/__reload").onmessage = () => {
  const u = new URL(location.href); u.searchParams.set("t", Math.round(window.__t || 0)); location.replace(u);
};
</script>`;
const types = { ".html": "text/html", ".ldr": "text/plain", ".js": "text/javascript" };
http.createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  if (url.pathname === "/__reload") {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
    clients.add(res); req.on("close", () => clients.delete(res));
    return;
  }
  const rel = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  const file = path.join(here, "out", name, path.normalize(rel));
  if (!file.startsWith(path.join(here, "out", name))) { res.writeHead(403).end(); return; }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404).end("not built yet"); return; }
    res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream" });
    res.end(file.endsWith(".html") ? buf.toString().replace("</body>", RELOAD + "</body>") : buf);
  });
}).listen(port, () => console.log(`brick-stage dev · http://localhost:${port}  (editing stories/${name}.mjs)`));

let timer;
for (const dir of [path.join(here, "stories"), path.join(here, "lib"), path.join(here, "..", "brick-check", "lib")]) {
  fs.watch(dir, { recursive: true }, () => { clearTimeout(timer); timer = setTimeout(rebuild, 120); });
}
rebuild();
