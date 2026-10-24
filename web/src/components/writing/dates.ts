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

/** What kind of piece this is, by its tags: a journal entry, a lab note, or an essay. */
export function kindOf(tags: readonly string[]): string {
  if (isJournal(tags)) return "Journal";
  if (tags.includes("lab notes") || tags.includes("lab-notes")) return "Lab note";
  return "Essay";
}

/**
 * "About 1 month ago", measured against the day the site was built so the
 * server render and the browser agree.
 */
export function ageOf(value: string | Date, builtAt: string): string {
  const days = Math.max(
    0,
    Math.round((Date.parse(`${builtAt}T00:00:00Z`) - Date.parse(isoDay(value))) / 86_400_000),
  );
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  if (days < 14) return "Last week";
  if (days < 30) return `${Math.round(days / 7)} weeks ago`;
  const months = Math.round(days / 30.4);
  if (months < 12) return months <= 1 ? "About 1 month ago" : `About ${months} months ago`;
  const years = Math.round(days / 365);
  return years <= 1 ? "About 1 year ago" : `About ${years} years ago`;
}
