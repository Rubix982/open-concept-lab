// Write a "someday" idea down in one line, without deciding anything else:
//
//   npm run idea -- "try making a kite"
//   npm run idea -- "a tool that …" --kind business --why "because …"
//
// Creates someday/YYYY-MM-DD-<short-name>.md with the front matter filled in
// and prints its path, so you can open it and keep writing if you want to.
// Kinds: business, try, learn, make (or b, t, l, m).
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = fileURLToPath(new URL("../someday/", import.meta.url));
const KINDS = { b: "business", t: "try", l: "learn", m: "make" };

const args = process.argv.slice(2);
let kind = "try";
let why;
const words = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--kind") kind = args[++i];
  else if (args[i] === "--why") why = args[++i];
  else words.push(args[i]);
}
kind = KINDS[kind] ?? kind;
const title = words.join(" ").trim();

if (!title) {
  console.error('Usage: npm run idea -- "the idea" [--kind business|try|learn|make] [--why "…"]');
  process.exit(1);
}
if (!Object.values(KINDS).includes(kind)) {
  console.error(`Unknown kind "${kind}". Use business, try, learn or make.`);
  process.exit(1);
}

// A local date, not UTC: an idea written at 1 a.m. belongs to the day you are in.
const now = new Date();
const day = [now.getFullYear(), now.getMonth() + 1, now.getDate()]
  .map((n, i) => String(n).padStart(i ? 2 : 4, "0"))
  .join("-");

// The first few words make the file name; a clash gets -2, -3, ...
const short =
  title
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .split("-")
    .slice(0, 6)
    .join("-") || "idea";
mkdirSync(dir, { recursive: true });
let file = path.join(dir, `${day}-${short}.md`);
for (let n = 2; existsSync(file); n++) file = path.join(dir, `${day}-${short}-${n}.md`);

// JSON strings are valid YAML double-quoted strings, so any text is safe here.
const lines = [
  "---",
  `title: ${JSON.stringify(title)}`,
  `kind: ${kind}`,
  "status: spark",
  ...(why ? [`why: ${JSON.stringify(why)}`] : []),
  "---",
  "",
];
writeFileSync(file, lines.join("\n"));
console.log(`Written down (${kind}): ${title}\n${path.relative(process.cwd(), file)}`);
