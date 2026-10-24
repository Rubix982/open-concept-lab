import type { WritingEntry } from "@site/plugins/lab-data";

/** Pieces tagged `journal` are written fast and read as a diary, not an argument. */
export const JOURNAL_TAG = "journal";

export function isJournal(tags: readonly string[]): boolean {
  return tags.includes(JOURNAL_TAG);
}

/** A date as YYYY-MM-DD, whatever it arrived as. */
export function isoDay(value: string | Date): string {
  return new Date(value).toISOString().slice(0, 10);
}

/** "24 Oct 2026" or "October 2026" — always UTC, so the build and the browser agree. */
export function formatDate(
  value: string | Date,
  options: Intl.DateTimeFormatOptions,
): string {
  return new Intl.DateTimeFormat("en-GB", { ...options, timeZone: "UTC" }).format(
    new Date(value),
  );
}

/**
 * Journal entries are numbered in the order they were written, so the number on
 * an entry never changes when a later one is added.
 */
export function journalNumber(
  writing: readonly WritingEntry[],
  slug: string,
): number | undefined {
  const journal = writing
    .filter((entry) => isJournal(entry.tags))
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const index = journal.findIndex((entry) => entry.slug === slug);
  return index === -1 ? undefined : index + 1;
}
