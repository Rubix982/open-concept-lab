// UX audit: walks Advisor Atlas in a browser (desktop and phone) and flags the small flaws that
// otherwise get found by screenshot. Run after UI changes:
//
//     make ux-audit            (or: node web/scripts/ux-audit.mjs [http://localhost:3000])
//
// Writes docs/ux-audit/latest.md (and screenshots of each page) and exits 1 when something is
// flagged. Checks, per page:
//   default-button   a button in the browser's grey default look (a missing style)
//   raw-code         a code where a name belongs: "sf1902", "CoI", ALL-CAPS titles and names
//   text-glitch      "(LRMs).At", "word ,", "))", ", ,", "undefined", "null", "NaN", "[object Object]"
//   zero-stat        a headline number that is 0 (often: no data, not zero)
//   same-values      five or more equal numbers (of 5 or more) in one list: a capped sample read as
//                    sizes. A list reviewed on purpose carries data-audit-ok="why".
//   long-list        more than 25 items shown at once with no "Show more"
//   overflow         the page scrolls sideways
//   unnamed-control  a button or input with no accessible name; an image with no alt text
//   slow-request     an API call over 4 s; failed-request: an API call that failed
//   page-error       a script error or a console error
// and, over all pages, the external sites linked to (nsf.gov is blocked from Pakistan, where most
// of its students are).
import { chromium } from "playwright";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.argv[2] || process.env.ATLAS_URL || "http://localhost:3000";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUT = path.join(ROOT, "docs", "ux-audit");
const SHOTS = path.join(OUT, "screens");
fs.mkdirSync(SHOTS, { recursive: true });

// Sites known to block visitors from Pakistan (where most of the app's students are)
const BLOCKED_FROM_PK = { "www.nsf.gov": "NSF award pages: 'This resource is not available in your region'" };

// A Playwright browser, or the newest one cached on this machine
function browserPath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const cache = path.join(os.homedir(), "Library", "Caches", "ms-playwright");
  if (!fs.existsSync(cache)) return undefined;
  const dirs = fs.readdirSync(cache).filter((d) => d.startsWith("chromium_headless_shell-")).sort().reverse();
  for (const d of dirs) {
    for (const sub of ["chrome-headless-shell-mac-arm64", "chrome-headless-shell-mac-x64", "chrome-headless-shell-linux64"]) {
      const p = path.join(cache, d, sub, "chrome-headless-shell");
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

const findings = []; // {page, check, detail}
const external = new Map(); // host -> count
const flag = (page, check, detail) => findings.push({ page, check, detail });

// Runs in the page: everything that can be judged from what is on screen
function inspect() {
  const out = [];
  const visible = (e) => !!(e.offsetParent || e.getClientRects().length) && getComputedStyle(e).visibility !== "hidden";
  const label = (e) => (e.innerText || e.value || e.getAttribute("aria-label") || e.placeholder || "").trim().replace(/\s+/g, " ").slice(0, 60);
  const where = (e) => {
    const h = e.closest("section, aside, dialog, .row, li")?.querySelector("h2, h3, .name, .hit");
    return h ? ` (in "${(h.innerText || "").trim().slice(0, 40)}")` : "";
  };
  for (const b of document.querySelectorAll("button")) {
    if (!visible(b)) continue;
    const s = getComputedStyle(b);
    const grey = /^rgb\((2[23]\d|24\d), (2[23]\d|24\d), (2[23]\d|24\d)\)$/.test(s.backgroundColor) && s.backgroundImage === "none";
    if (grey || /outset|inset/.test(s.borderStyle)) out.push(["default-button", `"${label(b)}"${where(b)}`]);
    if (!label(b) && !b.title) out.push(["unnamed-control", `button with no text or label${where(b)}`]);
  }
  for (const i of document.querySelectorAll("input:not([type=hidden]), select")) {
    if (!visible(i)) continue;
    const named = i.getAttribute("aria-label") || i.placeholder || (i.id && document.querySelector(`label[for="${i.id}"]`)) || i.closest("label");
    if (!named) out.push(["unnamed-control", `${i.tagName.toLowerCase()} with no label${where(i)}`]);
  }
  for (const img of document.querySelectorAll("img")) if (visible(img) && !img.hasAttribute("alt")) out.push(["unnamed-control", `image with no alt: ${img.src.slice(0, 60)}`]);

  // Text: walk the visible text of the main panels (not the map's own labels)
  const roots = [...document.querySelectorAll("aside, main, section, dialog[open], .results, .drawer-slot, header")];
  const seen = new Set();
  for (const r of roots) {
    const walker = document.createTreeWalker(r, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const t = n.textContent.replace(/\s+/g, " ").trim();
      if (t.length < 3 || seen.has(t) || !n.parentElement || !visible(n.parentElement)) continue;
      if (n.parentElement.closest(".mapboxgl-map, script, style, code")) continue;
      seen.add(t);
      if (/\bsf\d{3,4}\b/.test(t)) out.push(["raw-code", `area code shown: "${t.slice(0, 80)}"`]);
      if (/(^|[\s,(])CoI([\s,)]|$)/.test(t)) out.push(["raw-code", `role code shown: "${t.slice(0, 80)}"`]);
      const letters = t.replace(/[^A-Za-z]/g, "");
      if (letters.length > 20 && letters === letters.toUpperCase() && t.split(" ").length >= 4)
        out.push(["raw-code", `all capitals: "${t.slice(0, 80)}"`]);
      if (/[a-z)\]][.!?][A-Z][a-z]{2,}/.test(t) && !/https?:|www\.|\.[a-z]{2,4}\b|[A-Z]\.[A-Z]/.test(t))
        out.push(["text-glitch", `missing space after a full stop: "${t.match(/.{0,30}[a-z)\]][.!?][A-Z][a-z]{2,}.{0,10}/)?.[0]}"`]);
      if (/\w \s*[,;:](\s|$)/.test(t.replace(/\s+/g, " ")) && / [,;:](\s|$)/.test(t)) out.push(["text-glitch", `space before punctuation: "${t.match(/.{0,25} [,;:].{0,10}/)?.[0]}"`]);
      if (/\b(undefined|NaN)\b|\[object Object\]|(^|\s)null(\s|$)/.test(t)) out.push(["text-glitch", `"${t.slice(0, 80)}"`]);
      if (/\)\)|\(\(|\(\s*\)|,\s*,|(?<!\.)\.\s+\.(?!\.)|(?<!\.)\.\.(?!\.)/.test(t)) out.push(["text-glitch", `doubled or empty punctuation: "${t.match(/.{0,30}(\)\)|\(\(|\(\s*\)|,\s*,|\.\s*\.).{0,10}/)?.[0]}"`]);
    }
  }
  // Numbers: a 0 as a headline stat; five or more equal numbers in one list
  for (const dd of document.querySelectorAll("dd")) {
    if (visible(dd) && !dd.closest("[data-audit-ok]") && /^0$/.test(dd.innerText.trim())) out.push(["zero-stat", `"${dd.previousElementSibling?.innerText?.trim() ?? "?"}: 0"${where(dd)}`]);
  }
  for (const list of document.querySelectorAll("ul, ol, .chips")) {
    if (!visible(list) || list.closest("[data-audit-ok]")) continue; // reviewed on purpose (it says why)
    const nums = [...list.children].map((c) => (c.innerText.match(/(\d[\d,]*)\s*$/) || [])[1]).filter(Boolean);
    const counts = {};
    for (const n of nums) counts[n] = (counts[n] || 0) + 1;
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    if (top && top[1] >= 5 && nums.length >= 5 && Number(top[0].replace(/,/g, "")) >= 5) out.push(["same-values", `${top[1]} of ${nums.length} items read "${top[0]}"${where(list)}`]);
    const shown = [...list.children].filter((c) => c.tagName === "LI" && visible(c)).length;
    if (shown > 25) out.push(["long-list", `${shown} items at once${where(list)}`]);
  }
  if (document.documentElement.scrollWidth > window.innerWidth + 1)
    out.push(["overflow", `page is ${document.documentElement.scrollWidth}px wide in a ${window.innerWidth}px window`]);
  const links = [...document.querySelectorAll("a[href^='http']")].filter(visible).map((a) => new URL(a.href).host).filter((h) => h !== location.host);
  return { out, links };
}

async function audit(browser, name, viewport, steps) {
  const page = await browser.newPage({ viewport });
  await page.addInitScript(() => localStorage.setItem("atlas.tourSeen", "1"));
  const started = new Map();
  page.on("request", (r) => r.url().includes("/api/") && started.set(r, Date.now()));
  page.on("requestfinished", (r) => {
    if (!started.has(r)) return;
    const ms = Date.now() - started.get(r);
    if (ms > 4000) flag(name, "slow-request", `${(ms / 1000).toFixed(1)} s ${new URL(r.url()).pathname}${new URL(r.url()).search.slice(0, 60)}`);
  });
  page.on("requestfailed", (r) => r.url().includes("/api/") && !/aborted/i.test(r.failure()?.errorText ?? "") && flag(name, "failed-request", `${r.failure()?.errorText} ${r.url().slice(0, 100)}`));
  page.on("response", (r) => r.url().includes("/api/") && r.status() >= 400 && flag(name, "failed-request", `HTTP ${r.status()} ${r.url().slice(0, 100)}`));
  page.on("pageerror", (e) => flag(name, "page-error", e.message.slice(0, 160)));
  page.on("console", (m) => m.type() === "error" && !/mapbox|webgl|tile/i.test(m.text()) && flag(name, "page-error", `console: ${m.text().slice(0, 160)}`));
  let i = 0;
  for (const [label, act] of steps) {
    try {
      await act(page);
      await page.waitForTimeout(600);
      const { out, links } = await page.evaluate(inspect);
      for (const [check, detail] of out) flag(`${name} / ${label}`, check, detail);
      for (const h of links) external.set(h, (external.get(h) || 0) + 1);
      await page.screenshot({ path: path.join(SHOTS, `${name}-${++i}.png`) });
    } catch (e) {
      flag(`${name} / ${label}`, "step-failed", e.message.split("\n")[0].slice(0, 160));
    }
  }
  await page.close();
}

const ready = (sel, t = 120000) => (p) => p.waitForSelector(sel, { timeout: t });
const go = (q, sel) => async (p) => { await p.goto(BASE + q, { waitUntil: "domcontentloaded" }); await ready(sel)(p); };
const tab = (name, sel) => async (p) => { await p.locator(".uni-tabs button", { hasText: name }).click(); if (sel) await ready(sel)(p); await p.waitForTimeout(1500); };
const university = (id) => [
  ["overview", go(`/?u=${id}`, ".uni-tabs")],
  ["faculty", tab("Faculty", "ul.list > *")],
  ["funding", tab("Funding", ".held .grants li, .held p")],
  ["grant window", async (p) => { const b = p.locator(".held .grants li button.title").first(); if (await b.count()) { await b.click(); await ready("dialog.grant h2", 60000)(p); } }],
  ["scholarships", async (p) => { await p.keyboard.press("Escape"); await tab("Scholarships")(p); }],
];

const browser = await chromium.launch({ executablePath: browserPath(), args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const desk = { width: 1440, height: 900 };
const phone = { width: 390, height: 844 };
const t0 = Date.now();
await audit(browser, "home", desk, [
  ["first view", go("/", ".funding-teaser")],
  ["search", async (p) => { await p.getByRole("button", { name: "robot learning" }).click(); await ready(".fac-list li")(p); }],
  ["profile", async (p) => { await p.locator(".fac-list li button.hit").first().click(); await ready(".prof h2", 60000)(p); await p.waitForTimeout(2500); }],
  ["funding tab", go("/?q=malaria%20vaccine&view=funding", ".funding .lead-line")],
  ["funding overview", go("/?view=funding", ".funding .lead-line")],
]);
for (const id of ["carnegiemellonuniversity", "comsatsuniversityislamabad", "shanghaijiaotonguniversity", "universitycanterbury"])
  await audit(browser, id, desk, university(id));
await audit(browser, "pakistani-profile", desk, [
  ["profile", go(`/?u=universitypunjab&p=${encodeURIComponent("Abdul Nasir Khalid")}`, ".prof h2")],
]);
await audit(browser, "phone", phone, [
  ["first view", go("/", ".funding-teaser")],
  ["funding", go("/?q=solar%20cells&view=funding", ".funding .lead-line")],
  ["university", go("/?u=georgetownuniversity", ".uni-tabs")],
  ["university funding", tab("Funding", ".held .grants li, .held p")],
]);
await browser.close();

// The report: one line per finding, grouped by check, plus the external sites
const byCheck = {};
for (const f of findings) (byCheck[f.check] ??= []).push(f);
const unique = (list) => [...new Map(list.map((f) => [f.detail + "|" + f.page.split(" / ")[1], f])).values()];
let md = `# UX audit\n\n${new Date().toISOString().slice(0, 16).replace("T", " ")} UTC, ${BASE}, ${((Date.now() - t0) / 1000).toFixed(0)} s. `;
md += findings.length ? `**${unique(findings).length} findings.**\n` : "**Nothing flagged.**\n";
for (const [check, list] of Object.entries(byCheck).sort()) {
  md += `\n## ${check} (${unique(list).length})\n\n`;
  for (const f of unique(list).slice(0, 40)) md += `- ${f.page}: ${f.detail}\n`;
}
md += `\n## Sites linked to\n\n`;
for (const [h, n] of [...external].sort((a, b) => b[1] - a[1])) md += `- ${h} (${n} links)${BLOCKED_FROM_PK[h] ? ` **blocked from Pakistan**: ${BLOCKED_FROM_PK[h]}` : ""}\n`;
md += `\nScreenshots: docs/ux-audit/screens/.\n`;
fs.writeFileSync(path.join(OUT, "latest.md"), md);
console.log(md);
process.exit(findings.length ? 1 : 0);
