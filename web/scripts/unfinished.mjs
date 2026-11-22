#!/usr/bin/env node
// Refresh the commit strips on /unfinished.
//
//   npm run unfinished
//
// Reads every `repo` in data/unfinished.yml, asks GitHub (through the `gh` CLI,
// so private repos work too) for the dates of its commits on the default
// branch, and writes data/unfinished-activity.json: first and last commit,
// the total, and commits per month. The site never calls GitHub itself, so a
// build works offline; this file is the snapshot it draws from.

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { load as parseYaml } from "js-yaml";

const dataDir = join(dirname(fileURLToPath(import.meta.url)), "..", "data");
const listFile = join(dataDir, "unfinished.yml");
const outFile = join(dataDir, "unfinished-activity.json");

const entries = parseYaml(readFileSync(listFile, "utf8"))?.unfinished ?? [];
const repos = entries.map((e) => e.repo).filter(Boolean);
if (!repos.length) {
  console.log("No entry in data/unfinished.yml has a repo; nothing to fetch.");
  process.exit(0);
}

let previous = {};
try {
  previous = JSON.parse(readFileSync(outFile, "utf8"));
} catch {
  // first run
}

const out = {};
const today = new Date().toISOString().slice(0, 10);
for (const repo of repos) {
  let dates;
  try {
    const raw = execFileSync(
      "gh",
      ["api", `repos/${repo}/commits?per_page=100`, "--paginate", "--jq", ".[].commit.author.date"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
    );
    dates = raw.split("\n").filter(Boolean).map((d) => d.slice(0, 10)).sort();
  } catch (err) {
    // Keep the last good snapshot rather than dropping the strip.
    console.error(`${repo}: could not read commits (${String(err.stderr || err.message).trim()})`);
    if (previous[repo]) out[repo] = previous[repo];
    continue;
  }
  if (!dates.length) {
    console.error(`${repo}: no commits found`);
    continue;
  }
  const months = {};
  for (const d of dates) months[d.slice(0, 7)] = (months[d.slice(0, 7)] ?? 0) + 1;
  out[repo] = { first: dates[0], last: dates.at(-1), commits: dates.length, months, fetched: today };
  console.log(`${repo}: ${dates.length} commits, ${dates[0]} to ${dates.at(-1)}`);
}

writeFileSync(outFile, JSON.stringify(out, null, 2) + "\n");
console.log(`wrote ${outFile.replace(process.cwd() + "/", "")}`);
