/**
 * Is each generated threads page still the record it claims to be?
 *
 * A threads page is built from a project's `CARD.md` and `threads.md` by
 * `ai/tools/build_threads_page.py` and committed. Nothing reruns it, so it drifts
 * silently -- which is exactly what the evidence ledger had been doing for
 * weeks before anyone looked, and the reason that check exists.
 *
 * Same mechanism: the generator writes a digest of its sources into the page's
 * front matter and this recomputes it. A digest rather than modification times,
 * because `git checkout` writes every file at once and a time-based check would
 * pass on a fresh clone whatever the contents were.
 */
import { createHash } from "node:crypto";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repo = path.resolve(web, "..");
const notebook = path.join(web, "notebook");

/** Kept in step with SOURCES in build_lab_log.py, same order. */
const SOURCES = ["CARD.md", "threads.md"];

const fail = (msg) => {
  console.error(`\ncheck-threads-page: ${msg}\n`);
  process.exit(1);
};

let checked = 0;
for (const project of readdirSync(notebook)) {
  const page = path.join(notebook, project, "_threads.mdx");
  if (!existsSync(page)) continue;
  checked += 1;

  // The partial carries no front matter, so its digest lives beside it in
  // data/record.yml -- which the rail reads too, so one file cannot go stale
  // while the other does not.
  const rec = readFileSync(path.join(web, "data", "record.yml"), "utf8");
  const block = new RegExp(`^${project}:\\n(?:  .*\\n)*`, "m").exec(rec)?.[0] ?? "";
  const declared = /^\s*digest:\s*([0-9a-f]+)\s*$/m.exec(block)?.[1];
  if (!declared) {
    fail(
      `data/record.yml has no digest for ${project}.\n` +
        `    Regenerate it:  python3 ai/tools/build_threads_page.py ${project}`,
    );
  }

  const h = createHash("sha256");
  for (const s of SOURCES) {
    const p = path.join(repo, "ai", project, s);
    h.update(existsSync(p) ? readFileSync(p) : Buffer.alloc(0));
  }
  const actual = h.digest("hex").slice(0, 16);

  if (actual !== declared) {
    fail(
      `${project}'s threads page is older than the record it is generated from.\n` +
        `    page says ${declared}, the record hashes to ${actual}.\n\n` +
        `    Regenerate and commit it:\n` +
        `      python3 ai/tools/build_threads_page.py ${project}`,
    );
  }
}

console.log(
  checked
    ? `check-threads-page: ${checked} threads page(s) match their record`
    : "check-threads-page: no threads pages to check",
);
