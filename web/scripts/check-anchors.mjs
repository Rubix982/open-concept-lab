/**
 * Every in-page link on the built site lands somewhere.
 *
 * Docusaurus already has `onBrokenAnchors`, and it only knows about anchors it
 * generated itself — the headings. An id written by a React component, like the
 * `run-E-012` on a provenance row, is invisible to it, so it reports every link
 * to one as broken. Turning that check off would have cost the heading check
 * too, which on 18 November 2026 caught two cross-page links left pointing at
 * headings that had been reworded.
 *
 * This reads the built HTML instead, so it sees whatever actually shipped and
 * makes no distinction between an anchor a heading wrote and one a component
 * did. It runs after the build, not before, because that is when the HTML
 * exists.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const BUILD = new URL("../build/", import.meta.url).pathname;

function pages(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) pages(p, out);
    else if (name.endsWith(".html")) out.push(p);
  }
  return out;
}

/*
 * Two places this check cannot read, each for a stated reason. Anything added
 * here needs its reason written beside it, because an unexplained exclusion is
 * how a check quietly stops checking.
 *
 *   demos/    self-contained pages synced in from other projects. Some build
 *             their hrefs in inline JavaScript, so a literal `#' + id + '`
 *             sits in the HTML and is not a link at all.
 *   reading/  its rows are rendered after hydration, so none of their ids is
 *             in the static HTML. The page says so itself and registers them
 *             with Docusaurus's own checker; reading the HTML cannot see them.
 */
const SKIP = ["demos/", "reading/"];
const files = pages(BUILD).filter(
  (f) => !SKIP.some((d) => relative(BUILD, f).startsWith(d)),
);
let broken = 0;
let checked = 0;

for (const file of files) {
  const html = readFileSync(file, "utf8");
  const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));
  // `name` is still how a footnote back-reference marks its landing point.
  for (const m of html.matchAll(/\sname="([^"]+)"/g)) ids.add(m[1]);

  const seen = new Set();
  for (const m of html.matchAll(/href="#([^"]+)"/g)) {
    const raw = m[1];
    if (!raw || raw === "_" || seen.has(raw)) continue;
    seen.add(raw);
    checked += 1;
    // A link is written percent-encoded and an id is not, so compare decoded.
    let target = raw;
    try { target = decodeURIComponent(raw); } catch { /* keep the raw form */ }
    if (ids.has(raw) || ids.has(target)) continue;
    broken += 1;
    console.error(`  ${relative(BUILD, file)}\n     -> #${raw}`);
  }
}

if (broken) {
  console.error(`\ncheck-anchors: ${broken} link(s) point at an anchor that is not on the page.`);
  process.exit(1);
}
console.log(`check-anchors: ${checked} in-page links across ${files.length} pages all land.`);
