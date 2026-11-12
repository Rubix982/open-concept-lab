// Start a journal post in one line:
//
//   npm run journal -- "Learning to Tell a Story"
//   npm run journal -- "Learning to Tell a Story" --slug telling-a-story
//
// Creates blog/YYYY-MM-DD-<slug>.md with the front matter filled in (tagged
// journal) and prints its path and the address it will have on the site.
// A cover is optional: static/img/covers/<slug>.svg|png|jpg|webp.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = fileURLToPath(new URL("../blog/", import.meta.url));

const args = process.argv.slice(2);
let slug;
const words = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--slug") slug = args[++i];
  else words.push(args[i]);
}
const title = words.join(" ").trim();

if (!title) {
  console.error('Usage: npm run journal -- "The Title" [--slug short-name]');
  process.exit(1);
}

// A local date, not UTC: a post written at 1 a.m. belongs to the day you are in.
const now = new Date();
const day = [now.getFullYear(), now.getMonth() + 1, now.getDate()]
  .map((n, i) => String(n).padStart(i ? 2 : 4, "0"))
  .join("-");

const toSlug = (text) =>
  text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .split("-")
    .slice(0, 6)
    .join("-");
const base = toSlug(slug ?? title) || "journal";

// Slugs are the post's address, so they must be unique across every post, not
// just today's; a clash gets -2, -3, ...
mkdirSync(dir, { recursive: true });
const taken = new Set(
  readdirSync(dir)
    .filter((f) => /\.mdx?$/.test(f))
    .map((f) => readFileSync(path.join(dir, f), "utf8").match(/^slug:\s*(\S+)/m)?.[1])
    .filter(Boolean),
);
let short = base;
for (let n = 2; taken.has(short) || existsSync(path.join(dir, `${day}-${short}.md`)); n++) short = `${base}-${n}`;
const file = path.join(dir, `${day}-${short}.md`);

// JSON strings are valid YAML double-quoted strings, so any title is safe here.
const lines = [
  "---",
  `slug: ${short}`,
  `title: ${JSON.stringify(title)}`,
  "authors: [saif]",
  "tags: [journal]",
  `date: ${day}`,
  "---",
  "",
  "",
];
writeFileSync(file, lines.join("\n"));
console.log(`Started: ${title}\n${path.relative(process.cwd(), file)}\nOn the site at /writing/${short}`);
