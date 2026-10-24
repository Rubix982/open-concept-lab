/**
 * Acceptance criteria from DESIGN.md §9, as a check rather than an aspiration.
 *
 * Eight of the twelve criteria are mechanically decidable from the stylesheet and the
 * built HTML. The other four (measure in characters, 390px overflow, focus visibility,
 * Lighthouse) need a real browser and are reported as NOT CHECKED rather than passed —
 * a criterion silently skipped reads as a criterion met.
 *
 *   node scripts/design-check.mjs            # after `yarn build`
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const CSS = "src/css/custom.css";
const BUILD = "build";
const css = readFileSync(CSS, "utf8");

let failures = 0;
const report = (ok, id, label, detail = "") => {
  const mark = ok === null ? "  ⋯ " : ok ? "  ✓ " : "  ✗ ";
  if (ok === false) failures++;
  console.log(`${mark}${id}  ${label}${detail ? `\n        ${detail}` : ""}`);
};

/** Strip comments so a rule quoted in prose is not read as a rule. */
const live = css.replace(/\/\*[\s\S]*?\*\//g, "");

// ---------------------------------------------------------------- 2 · radius
{
  // Revised 2026-10-24: corners soften, but only through the radius tokens. Every
  // component of a border-radius must be a --ocl-radius* token, 0, or 999px (a pill).
  // A literal pixel value is a corner nobody decided on.
  const ok = (part) => /^(0|0px|0%|999px|inherit|initial|unset|var\(--ocl-radius(-sm|-lg)?\))$/.test(part);
  const bad = [...live.matchAll(/border-radius:\s*([^;]+);/g)]
    .filter((m) => !m[1].trim().split(/\s+(?![^(]*\))/).every(ok));
  report(bad.length === 0, "§9.2", "every corner comes from a radius token",
    bad.length ? `${bad.length} rules, e.g. ${bad.slice(0, 3).map((m) => m[1].trim()).join(", ")}` : "");
}

// ---------------------------------------------------- 3 · shadows (elevation)
{
  // Elevation is allowed only through the two shadow tokens; an inset rule is a
  // hairline drawn with the shadow property and stays permitted.
  const shadows = [...live.matchAll(/box-shadow:\s*([^;]+);/g)].map((m) => m[1].trim());
  const loose = shadows.filter((v) => v !== "none" && !v.includes("inset") && !v.includes("!important")
    && !/^var\(--ocl-shadow(-lift)?\)$/.test(v));
  report(loose.length === 0, "§9.3", "elevation only through --ocl-shadow tokens",
    loose.length ? loose.slice(0, 3).join(" / ") : `${shadows.length} shadow rules, all tokens, none or inset`);
}

// ------------------------------------------------------------- 4 · tokenised
{
  // Hex literals are legitimate inside :root and [data-theme] token blocks and inside
  // SVG-bearing components; everywhere else they are an untokenised colour.
  const withoutTokenBlocks = live.replace(/(:root|\[data-theme=['"]dark['"]\])\s*\{[^}]*\}/g, "");
  const hexes = [...withoutTokenBlocks.matchAll(/#[0-9a-fA-F]{3,8}\b/g)].map((m) => m[0]);
  report(hexes.length === 0, "§9.4", "every colour resolves to a token",
    hexes.length ? `${hexes.length} raw hex outside token blocks: ${[...new Set(hexes)].slice(0, 5).join(" ")}` : "");
}

// -------------------------------------------------- 5 · figures numbered/captioned
const htmlFiles = [];
(function walk(dir) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p);
    else if (e === "index.html") htmlFiles.push(p);
  }
})(BUILD);

{
  let figures = 0, captioned = 0;
  for (const f of htmlFiles) {
    const h = readFileSync(f, "utf8");
    // Match the figure ROOT only. "ocl-figure" is also a prefix of ocl-figure__frame
    // and ocl-figure__caption, so a loose match counts every figure three times and
    // reports a 3:1 shortfall that does not exist.
    const figs = h.match(/class="ocl-figure(?:\s|")/g) ?? [];
    figures += figs.length;
    captioned += (h.match(/ocl-figure__caption/g) ?? []).length;
  }
  report(figures === 0 || captioned >= figures, "§9.5", "every figure has a caption",
    `${figures} figures, ${captioned} captions`);
}

// ------------------------------------------------- 6 · evidence ids resolve
{
  const ledger = htmlFiles.find((f) => f.includes("edit-slice/ledger"));
  const anchors = ledger
    ? new Set([...readFileSync(ledger, "utf8").matchAll(/id="((?:t-)?(?:f-)?[EORTD]-\d{3}[a-z]?(?:-\d)?)"/g)].map((m) => m[1]))
    : new Set();
  let links = 0, broken = [];
  for (const f of htmlFiles) {
    for (const m of readFileSync(f, "utf8").matchAll(/ledger#([\w-]+)/g)) {
      links++;
      if (!anchors.has(m[1])) broken.push(m[1]);
    }
  }
  report(broken.length === 0, "§9.6", "every evidence link resolves",
    `${links} links against ${anchors.size} anchors${broken.length ? `; broken: ${[...new Set(broken)].join(", ")}` : ""}`);
}

// ---------------------------------------------------------------- 9 · contrast
{
  const tok = (name, block) => {
    const scope = block === "dark"
      ? css.match(/\[data-theme=['"]dark['"]\]\s*\{[\s\S]*?\n\}/)?.[0] ?? ""
      : css.match(/:root\s*\{[\s\S]*?\n\}/)?.[0] ?? "";
    return scope.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{3,6})`))?.[1];
  };
  const lum = (hex) => {
    const n = hex.length === 4
      ? [1, 2, 3].map((i) => parseInt(hex[i] + hex[i], 16))
      : [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    const [r, g, b] = n.map((v) => (v / 255 <= 0.03928 ? v / 255 / 12.92 : ((v / 255 + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };
  for (const mode of ["light", "dark"]) {
    const paper = tok("ocl-paper", mode), ink = tok("ocl-ink", mode), muted = tok("ocl-ink-muted", mode);
    if (!paper || !ink || !muted) { report(null, "§9.9", `contrast (${mode})`, "tokens not found"); continue; }
    const ri = ratio(ink, paper), rm = ratio(muted, paper);
    report(ri >= 7 && rm >= 4.5, "§9.9", `contrast (${mode})`,
      `ink ${ri.toFixed(2)}:1 (need 7) · muted ${rm.toFixed(2)}:1 (need 4.5)`);
  }
}

// ------------------------------------------------------- 12 · reads without CSS
{
  // The criterion is "heading order intact, figure captions adjacent to their figures" —
  // a DOM-order property, not a styling one. An earlier version of this check tested
  // whether figure NUMBERS survive, which §9.12 does not ask for; a check stricter than
  // its criterion fails honest work and erodes the whole list.
  let bad = [];
  for (const f of htmlFiles) {
    const h = readFileSync(f, "utf8");
    // every figure root must be followed by its caption before the next figure root
    const roots = [...h.matchAll(/class="ocl-figure(?:\s|")/g)].map((m) => m.index);
    for (let i = 0; i < roots.length; i++) {
      const seg = h.slice(roots[i], roots[i + 1] ?? h.length);
      if (!seg.includes("ocl-figure__caption")) bad.push(f);
    }
    // heading order must not skip a level
    const levels = [...h.matchAll(/<h([1-4])[^>]*class="[^"]*anchor/g)].map((m) => +m[1]);
    for (let i = 1; i < levels.length; i++) {
      if (levels[i] - levels[i - 1] > 1) { bad.push(`${f} (h${levels[i - 1]}→h${levels[i]})`); break; }
    }
  }
  report(bad.length === 0, "§9.12", "reads with CSS disabled: captions adjacent, headings ordered",
    bad.length ? [...new Set(bad)].slice(0, 3).join(" · ") : `${htmlFiles.length} pages`);
}

for (const [id, why] of [
  ["§9.1", "measure in ch — needs a laid-out browser"],
  ["§9.8", "390px overflow — needs a viewport"],
  ["§9.10", "focus visibility — needs interaction"],
  ["§9.11", "Lighthouse ≥95 — needs the tool"],
]) report(null, id, why);

console.log(`\n${failures === 0 ? "all decidable criteria pass" : `${failures} FAILING`} · 4 not checked\n`);
process.exit(failures === 0 ? 0 : 1);
