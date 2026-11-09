#!/usr/bin/env node
/**
 * Every paper page carries the same eight sections, in the same order.
 *
 * The sections cannot live in the <Paper> component, which is where the rest of
 * the template lives. Docusaurus builds the contents rail from the markdown
 * syntax tree, and a heading emitted by a React component never appears in it —
 * the page would render correctly with an empty rail, which is the kind of
 * failure nobody notices for a month. So the headings stay as markdown and the
 * order is enforced here instead.
 *
 * A page is a paper if its front matter has a `paper:` key.
 *
 * Run by `prebuild`, so a divergent page fails the build rather than shipping.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const SECTIONS = [
  "Introduction",
  "Related work",
  "Methods",
  "Implementation",
  "Results",
  "Findings and claims",
  "Limitations",
  "Conclusion",
];

const TAIL = ["References"];

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith(".md") || name.endsWith(".mdx")) out.push(p);
  }
  return out;
}

/** The front matter block, as raw text. Not parsed — we only need one key. */
function frontMatter(text) {
  if (!text.startsWith("---")) return "";
  const end = text.indexOf("\n---", 3);
  return end === -1 ? "" : text.slice(3, end);
}

function check(path) {
  const text = readFileSync(path, "utf8");
  const fm = frontMatter(text);
  if (!/^paper:\s*$/m.test(fm)) return null;

  const body = text.slice(fm.length + 6);
  const headings = [...body.matchAll(/^## +(.+)$/gm)].map((m) => m[1].trim());

  const numbered = headings
    .map((h) => h.match(/^(\d+)\.\s+(.+)$/))
    .filter(Boolean)
    .map((m) => ({ n: Number(m[1]), name: m[2] }));

  const faults = [];

  SECTIONS.forEach((name, i) => {
    const want = i + 1;
    const got = numbered.find((s) => s.n === want);
    if (!got) {
      faults.push(`missing  §${want}. ${name}`);
    } else if (got.name.toLowerCase() !== name.toLowerCase()) {
      faults.push(`§${want} is "${got.name}" — the template says "${name}"`);
    }
  });

  for (const s of numbered) {
    if (s.n > SECTIONS.length) {
      faults.push(`§${s.n} "${s.name}" — the template has ${SECTIONS.length} sections`);
    }
  }

  const order = numbered.map((s) => s.n);
  if (order.join(",") !== [...order].sort((a, b) => a - b).join(",")) {
    faults.push(`sections are out of order on the page: ${order.join(", ")}`);
  }

  for (const t of TAIL) {
    if (!headings.some((h) => h.toLowerCase() === t.toLowerCase())) {
      faults.push(`missing  ${t}`);
    }
  }

  const appendices = headings.filter((h) => /^Appendix [A-Z]\b/.test(h));
  if (appendices.length < 3) {
    faults.push(
      `${appendices.length} appendices — the template has three: the derivations, the provenance of every number, the readiness table`,
    );
  }

  return { path, faults };
}

const roots = process.argv.slice(2);
const files = (roots.length ? roots : ["notebook", "blog"])
  .filter((d) => {
    try {
      return statSync(d).isDirectory();
    } catch {
      return false;
    }
  })
  .flatMap(walk);

const results = files.map(check).filter(Boolean);

if (results.length === 0) {
  console.log("check-papers: no paper pages found");
  process.exit(0);
}

let bad = 0;
for (const r of results) {
  if (r.faults.length === 0) {
    console.log(`check-papers: ${r.path} — conforms`);
    continue;
  }
  bad += 1;
  console.error(`\ncheck-papers: ${r.path}`);
  for (const f of r.faults) console.error(`    ${f}`);
}

if (bad) {
  console.error(
    `\n${bad} of ${results.length} paper pages diverge from the template.` +
      `\nThe order is Introduction, Related work, Methods, Implementation, Results,` +
      `\nFindings and claims, Limitations, Conclusion — then References and three` +
      `\nappendices. A section with nothing in it says so in one line; it is not` +
      `\nremoved, because a removed section looks like an oversight.\n`,
  );
  process.exit(1);
}

console.log(`check-papers: ${results.length} paper page(s) conform`);
