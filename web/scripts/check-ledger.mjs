/**
 * Is the generated evidence ledger still the record it claims to be?
 *
 * `notebook/edit-slice/ledger.md` is built from three files in `ai/edit-slice` by
 * `build_ledger.py` and committed. Nothing reruns it, so it goes stale without saying
 * so: the record grows, and the site keeps showing a version of the project that
 * stopped being true. It had drifted by several decisions and threads before anyone
 * noticed, and the only reason anyone noticed was a regeneration for an unrelated fix.
 *
 * The generator writes a digest of its three sources into the page's front matter.
 * This recomputes it and fails when the two disagree.
 *
 * A digest rather than modification times: `git checkout` writes every file at once,
 * so a time-based check passes on a fresh clone whatever the contents are — a check
 * that cannot fail, which is a fault this repo has already paid for three times.
 */
import { createHash } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repo = path.resolve(web, "..");
const page = path.join(web, "notebook/edit-slice/ledger.md");

/** Kept in step with SOURCES in build_ledger.py, same order. */
const SOURCES = [
  "ai/edit-slice/agents/shared/decisions.md",
  "ai/edit-slice/agents/shared/findings.md",
  "ai/edit-slice/threads.md",
];

const fail = (msg) => {
  console.error(`\ncheck-ledger: ${msg}\n`);
  process.exit(1);
};

if (!existsSync(page)) fail(`${path.relative(repo, page)} is missing.`);

const text = readFileSync(page, "utf8");
const declared = /^source_digest:\s*([0-9a-f]+)\s*$/m.exec(text)?.[1];
if (!declared) {
  fail(
    `notebook/edit-slice/ledger.md has no source_digest in its front matter.\n` +
      `    Regenerate it:  cd ai/edit-slice && python agents/engineer/workspace/build_ledger.py`,
  );
}

const missing = SOURCES.filter((s) => !existsSync(path.join(repo, s)));
if (missing.length) fail(`source file(s) missing: ${missing.join(", ")}`);

const h = createHash("sha256");
for (const s of SOURCES) h.update(readFileSync(path.join(repo, s)));
const actual = h.digest("hex").slice(0, 16);

if (actual !== declared) {
  fail(
    `the evidence ledger is older than the record it is generated from.\n` +
      `    page says ${declared}, the record hashes to ${actual}.\n\n` +
      `    Regenerate and commit both outputs:\n` +
      `      cd ai/edit-slice && source .venv/bin/activate\n` +
      `      python agents/engineer/workspace/build_ledger.py`,
  );
}

console.log("check-ledger: the evidence ledger matches the record");
