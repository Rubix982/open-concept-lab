import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, WritingEntry } from "@site/plugins/lab-data";
import { formatDate, isJournal, isoDay } from "./dates";

const WEEKS = 26;
const DAY_MS = 86_400_000;

/** Monday of the week containing `day`, at UTC midnight. */
function weekStart(day: Date): Date {
  const offset = (day.getUTCDay() + 6) % 7;
  return new Date(day.getTime() - offset * DAY_MS);
}

/** Four steps of ink, by how much was written that day. */
function level(words: number): 1 | 2 | 3 | 4 {
  if (words < 600) return 1;
  if (words < 1500) return 2;
  if (words < 3000) return 3;
  return 4;
}

type Cell = { iso: string; entries: WritingEntry[]; future: boolean };

/**
 * The last half-year as a grid of days: a column per week, Monday at the top.
 * The point is cadence — whether the writing is a practice or an event — so a
 * filled square is a day something was written, darker for more words.
 */
export default function WritingDesk(): ReactNode {
  const { writing, builtAt } = usePluginData("ocl-lab-data") as LabData;
  if (writing.length === 0) {
    return null;
  }

  const byDay = new Map<string, WritingEntry[]>();
  for (const entry of writing) {
    const day = isoDay(entry.date);
    byDay.set(day, [...(byDay.get(day) ?? []), entry]);
  }

  const today = new Date(`${builtAt}T00:00:00Z`);
  const first = new Date(weekStart(today).getTime() - (WEEKS - 1) * 7 * DAY_MS);

  const weeks: Cell[][] = [];
  const months: { label: string; column: number }[] = [];
  for (let w = 0; w < WEEKS; w++) {
    const week: Cell[] = [];
    for (let d = 0; d < 7; d++) {
      const date = new Date(first.getTime() + (w * 7 + d) * DAY_MS);
      const iso = isoDay(date);
      week.push({ iso, entries: byDay.get(iso) ?? [], future: date > today });
      // a month is labelled on the week holding its 1st, unless the label
      // before it is too close to leave room
      const previous = months[months.length - 1];
      if (date.getUTCDate() === 1 && (!previous || w + 1 - previous.column >= 3)) {
        months.push({ label: formatDate(date, { month: "short" }), column: w + 1 });
      }
    }
    weeks.push(week);
  }

  const words = writing.reduce((sum, entry) => sum + entry.words, 0);
  const journal = writing.filter((entry) => isJournal(entry.tags)).length;
  const since = writing[writing.length - 1].date;
  const latest = writing[0];

  return (
    <section className="ocl-desk" aria-label="Writing at a glance">
      <div className="ocl-desk__stats">
        <p>
          <span className="ocl-desk__figure">{writing.length}</span>
          {writing.length === 1 ? "piece" : "pieces"}
        </p>
        <p>
          <span className="ocl-desk__figure">{words.toLocaleString("en-GB")}</span>
          words
        </p>
        {journal > 0 ? (
          <p>
            <span className="ocl-desk__figure">{journal}</span>
            journal {journal === 1 ? "entry" : "entries"}
          </p>
        ) : null}
        <p className="ocl-desk__since">
          Writing since {formatDate(since, { month: "long", year: "numeric" })}.
          Latest: <Link to={latest.permalink}>{latest.title}</Link>
        </p>
      </div>

      <div className="ocl-desk__calendar">
        <div
          className="ocl-desk__months"
          style={{ gridTemplateColumns: `repeat(${WEEKS}, 1fr)` }}
          aria-hidden="true"
        >
          {months.map((m) => (
            <span key={`${m.label}-${m.column}`} style={{ gridColumn: m.column }}>
              {m.label}
            </span>
          ))}
        </div>
        <div
          className="ocl-desk__grid"
          style={{ gridTemplateColumns: `repeat(${WEEKS}, 1fr)` }}
          role="img"
          aria-label={`${writing.length} pieces written; one square per day over the last ${WEEKS} weeks`}
        >
          {weeks.flat().map((cell) => {
            if (cell.future) {
              return <span key={cell.iso} className="ocl-desk__day ocl-desk__day--future" />;
            }
            const isToday = cell.iso === builtAt;
            const className = `ocl-desk__day${isToday ? " ocl-desk__day--today" : ""}`;
            if (cell.entries.length === 0) {
              return <span key={cell.iso} className={className} />;
            }
            const entry = cell.entries[0];
            const dayWords = cell.entries.reduce((sum, e) => sum + e.words, 0);
            const label = `${formatDate(cell.iso, { day: "numeric", month: "short" })}: ${cell.entries
              .map((e) => e.title)
              .join("; ")}`;
            return (
              <Link
                key={cell.iso}
                to={entry.permalink}
                title={label}
                aria-label={label}
                className={`${className} ocl-desk__day--ink-${level(dayWords)}${
                  cell.entries.some((e) => isJournal(e.tags)) ? " ocl-desk__day--journal" : ""
                }`}
              />
            );
          })}
        </div>
        <p className="ocl-desk__key" aria-hidden="true">
          <span>Less</span>
          {[1, 2, 3, 4].map((n) => (
            <span key={n} className={`ocl-desk__day ocl-desk__day--ink-${n}`} />
          ))}
          <span>More words</span>
          <span className="ocl-desk__day ocl-desk__day--ink-2 ocl-desk__day--journal" />
          <span>Journal</span>
        </p>
      </div>
    </section>
  );
}
