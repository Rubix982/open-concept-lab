#!/usr/bin/env node
// node new.mjs my-story "My Story"  — starts a story from the template.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2];
if (!name || !/^[a-z0-9-]+$/.test(name)) { console.log('usage: node new.mjs my-story "My Story"   (lower-case letters, digits and dashes)'); process.exit(1); }
const title = process.argv[3] || name.split("-").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
const target = path.join(here, "stories", `${name}.mjs`);
try { await fs.access(target); console.log(`stories/${name}.mjs already exists — pick another name`); process.exit(1); } catch {}
const src = await fs.readFile(path.join(here, "stories", "_template.mjs"), "utf8");
await fs.writeFile(target, src.replaceAll("__TITLE__", title).replaceAll("__NAME__", name));
console.log(`created stories/${name}.mjs\nnext: node dev.mjs ${name}   then open http://localhost:5173`);
