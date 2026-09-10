#!/usr/bin/env node
/**
 * Copies standalone HTML pages listed in data/built.yml into static/demos/, so
 * <Embed src="/demos/<name>/index.html"> serves them from this site's own
 * origin. A page deployed elsewhere needs none of this — embed it by URL.
 *
 * A directory source is copied wholesale (for a page with sibling assets);
 * a single .html file is copied to <name>/index.html.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load as parseYaml } from "js-yaml";

const siteDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(siteDir, "..");
const outDir = path.join(siteDir, "static", "demos");

const manifestPath = path.join(siteDir, "data", "built.yml");
const { built } = parseYaml(await fs.readFile(manifestPath, "utf8"));
// Entries with a `url` are hosted elsewhere; nothing to copy.
const demos = built.filter((entry) => entry.from);

await fs.rm(outDir, { recursive: true, force: true });
await fs.mkdir(outDir, { recursive: true });

let copied = 0;
const missing = [];

for (const demo of demos) {
  const source = path.resolve(repoRoot, demo.from);
  let stat;
  try {
    stat = await fs.stat(source);
  } catch {
    missing.push(demo.from);
    continue;
  }

  const target = path.join(outDir, demo.name);
  if (stat.isDirectory()) {
    await fs.cp(source, target, { recursive: true });
  } else {
    await fs.mkdir(target, { recursive: true });
    await fs.copyFile(source, path.join(target, "index.html"));
  }
  copied += 1;
  console.log(`  ${demo.from} -> /demos/${demo.name}/index.html`);
}

console.log(`synced ${copied} demo${copied === 1 ? "" : "s"} into static/demos/`);
if (missing.length > 0) {
  console.warn(
    `not found, skipped: ${missing.join(", ")}\n` +
      `Fix the path in data/built.yml or drop the entry.`,
  );
}
