import { useEffect, useState, type ReactNode } from "react";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Venue } from "@site/plugins/lab-data";

/**
 * Where work on model internals is judged, as cards with a filter above them —
 * the arrangement `built` and `reading` already use, and the classes are theirs
 * rather than a second set.
 *
 * This was a four-column table first. One of its columns held a single word and
 * another held a paragraph, so it could not fit the reading measure and stuck
 * out past every line above it. A card holds the same fields without the grid:
 * what each venue asks for is prose, and prose is what a card is for.
 *
 * One column, at the width of the text around it. The site's wider card grids
 * are on full-width pages; here a second column would buy two short rows and
 * cost the page its one right edge, which is the thing that was wrong before.
 *
 * Funding sits in the same list as the venues it is filtered beside, because
 * the alternative was a prose section below, and a claim nobody has verified is
 * safer inside a list that marks verification than in a paragraph that asks the
 * reader to remember.
 */
const KINDS: { key: Venue["kind"] | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "conference", label: "Conferences" },
  { key: "journal", label: "Journals" },
  { key: "track", label: "Tracks" },
  { key: "workshop", label: "Workshops" },
  { key: "competition", label: "Competitions" },
  { key: "funding", label: "Funding" },
];

/** Soonest deadline first; rolling journals, which have none, last. */
function byDeadline(a: Venue, b: Venue): number {
  if (a.deadline && b.deadline) return a.deadline.localeCompare(b.deadline);
  return a.deadline ? -1 : b.deadline ? 1 : 0;
}

const ARCHIVAL: Record<string, string> = {
  no: "non-archival",
  yes: "archival",
  choice: "archival or not, author's choice",
};

function VenueName({ venue }: { venue: Venue }): ReactNode {
  return venue.url ? (
    <a href={venue.url} target="_blank" rel="noreferrer">
      {venue.name}
    </a>
  ) : (
    <>{venue.name}</>
  );
}

function VenueCard({ venue }: { venue: Venue }): ReactNode {
  return (
    <article className="ocl-venue">
      <header className="ocl-venue__head">
        <h3 className="ocl-venue__name">
          <VenueName venue={venue} />
        </h3>
        <span className="ocl-venue__series">{venue.series}</span>
      </header>

      {venue.due ? <p className="ocl-venue__due">Due {venue.due}</p> : null}

      <VenueBody venue={venue} />
    </article>
  );
}

function VenueBody({ venue, withAsks = true }: { venue: Venue; withAsks?: boolean }): ReactNode {
  return (
    <>
      <p className="ocl-venue__when">
        {venue.when}
        {venue.where ? ` · ${venue.where}` : ""}
      </p>

      {withAsks ? <p className="ocl-venue__asks">{venue.asks}</p> : null}

      {venue.note ? <p className="ocl-venue__note">{venue.note}</p> : null}

      <footer className="ocl-venue__foot">
        {venue.kind !== "funding" ? (
          <span className="ocl-pill">{ARCHIVAL[venue.archival] ?? venue.archival}</span>
        ) : null}
        {venue.platform ? <span className="ocl-pill">on {venue.platform}</span> : null}
        {venue.paper ? (
          <a className="ocl-venue__paper" href={venue.paper} target="_blank" rel="noreferrer">
            its own paper ↗
          </a>
        ) : null}
        {venue.verified ? (
          <span className="ocl-check" title="Date, place and terms read off the venue's own page">
            checked
          </span>
        ) : (
          <span
            className="ocl-check ocl-check--no"
            title="Every description of this came from somewhere secondhand — do not cite or plan around it"
          >
            unchecked
          </span>
        )}
      </footer>
    </>
  );
}

/*
 * The timeline view: one line per venue in deadline order, opening into the
 * card. A page used for pacing is read for "what is next and how long do I
 * have", and eighteen full cards put the answer to that six screens deep.
 *
 * Days left are counted in the reader's browser, after the page has loaded,
 * because the build runs on one day and the page is read on another. Until
 * then the rows show dates only, which is what the server-rendered HTML holds.
 */
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAY = 86_400_000;

/**
 * Two readings of the same list. Looking ahead, a row is a deadline and its
 * second line is what is due. Looking back, a row is the event and its second
 * line is what the venue asked for, because that is what a look-back is read for.
 */
type Mode = "deadlines" | "events";

const dateOf = (v: Venue, mode: Mode): string | undefined => (mode === "events" ? v.held : v.deadline);

function parseDay(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** A checked date gets its day; an estimated one only its month, since the day would be invented. */
function dateLabel(v: Venue, mode: Mode): string {
  const iso = dateOf(v, mode);
  if (!iso) return "—";
  const d = parseDay(iso);
  return v.verified ? `${d.getDate()} ${MONTHS[d.getMonth()]}` : `~${MONTHS[d.getMonth()]}`;
}

function daysLeft(v: Venue, mode: Mode, today: Date): number | null {
  const iso = dateOf(v, mode);
  return iso ? Math.round((parseDay(iso).getTime() - today.getTime()) / DAY) : null;
}

function leftLabel(n: number, estimated: boolean, mode: Mode): string {
  if (n < 0) return mode === "events" ? "held" : "closed";
  if (n === 0) return "today";
  if (n === 1) return "tomorrow";
  const s = n < 60 ? `${n} days` : n < 120 ? `${Math.round(n / 7)} weeks` : `${Math.round(n / 30.4)} months`;
  return estimated ? `~${s}` : s;
}

function VenueRow({ venue, today, mode }: { venue: Venue; today: Date | null; mode: Mode }): ReactNode {
  const n = today ? daysLeft(venue, mode, today) : null;
  const soon = mode === "deadlines" && n !== null && n >= 0 && n <= 30 && venue.verified;
  const second = mode === "events" ? venue.asks : venue.due;
  return (
    <details className={`ocl-due${soon ? " ocl-due--soon" : ""}`} id={venue.id}>
      <summary className="ocl-due__row">
        <span className="ocl-due__date">
          <span className="ocl-due__day">{dateLabel(venue, mode)}</span>
          <span className="ocl-due__left">{n !== null ? leftLabel(n, !venue.verified, mode) : "\u00a0"}</span>
        </span>
        <span className="ocl-due__what">
          <span className="ocl-due__name">
            {venue.name}
            <span className="ocl-due__series">{venue.series}</span>
            {mode === "events" && !venue.verified ? (
              <span className="ocl-check ocl-check--no ocl-due__flag">unchecked</span>
            ) : null}
          </span>
          {second ? <span className="ocl-due__text">{second}</span> : null}
        </span>
        <span className="ocl-due__kind">{venue.kind}</span>
      </summary>
      <div className="ocl-due__body">
        <VenueBody venue={venue} withAsks={mode !== "events"} />
        {venue.url ? (
          <p className="ocl-due__link">
            <a href={venue.url} target="_blank" rel="noreferrer">
              {new URL(venue.url).hostname.replace(/^www\./, "")} ↗
            </a>
          </p>
        ) : null}
      </div>
    </details>
  );
}

function Timeline({ venues, mode }: { venues: Venue[]; mode: Mode }): ReactNode {
  const [today, setToday] = useState<Date | null>(null);
  useEffect(() => {
    const now = new Date();
    setToday(new Date(now.getFullYear(), now.getMonth(), now.getDate()));
    // A link to one venue opens its row, not just scrolls to it.
    const hash = decodeURIComponent(window.location.hash.slice(1));
    if (hash) document.getElementById(hash)?.setAttribute("open", "");
  }, []);

  const row = (v: Venue) => (
    <li key={v.id}>
      <VenueRow venue={v} today={today} mode={mode} />
    </li>
  );
  const group = (label: string, list: Venue[]) =>
    list.length
      ? [
          <li key={`g-${label}`} className="ocl-due__group">
            {label}
          </li>,
          ...list.map(row),
        ]
      : [];

  const dated = venues
    .filter((v) => dateOf(v, mode))
    .sort((a, b) => dateOf(a, mode)!.localeCompare(dateOf(b, mode)!));
  const undated = venues.filter((v) => !dateOf(v, mode));

  // Looking back, a past event stays where it fell; only deadlines close.
  if (mode === "events") {
    return (
      <ol className="ocl-due-list">
        {dated.map(row)}
        {group("No date", undated)}
      </ol>
    );
  }

  const closed = today ? dated.filter((v) => (daysLeft(v, mode, today) ?? 0) < 0) : [];
  const ahead = dated.filter((v) => !closed.includes(v));

  const rows: ReactNode[] = [];
  let year = "";
  for (const v of ahead) {
    const y = v.deadline!.slice(0, 4);
    if (y !== year) {
      year = y;
      rows.push(
        <li key={`y${y}`} className="ocl-due__group">
          {y}
        </li>,
      );
    }
    rows.push(row(v));
  }

  return (
    <ol className="ocl-due-list">
      {rows}
      {group("No fixed date", undated)}
      {group("Closed", closed)}
    </ol>
  );
}

export default function Venues({
  year = 2026,
  view = "cards",
}: {
  year?: number;
  view?: "cards" | "timeline" | "lookback";
}): ReactNode {
  const all = (usePluginData("ocl-lab-data") as LabData).venues;
  const [kind, setKind] = useState<Venue["kind"] | "all">("all");

  // One edition per page. A page planning ahead reads in deadline order; the
  // look back keeps the order the file was written in.
  const venues = all.filter((v) => v.year === year);
  if (year > 2026) venues.sort(byDeadline);

  const shown = kind === "all" ? venues : venues.filter((v) => v.kind === kind);
  const count = (k: Venue["kind"] | "all") =>
    k === "all" ? venues.length : venues.filter((v) => v.kind === k).length;
  const kinds = KINDS.filter((k) => k.key === "all" || count(k.key) > 0);

  return (
    <div className="ocl-venues">
      {view === "lookback" ? null : (
        <div className="ocl-filter__areas" role="group" aria-label="Kind of venue">
          {kinds.map((k) => (
            <button
              key={k.key}
              type="button"
              className="ocl-filter__chip"
              aria-pressed={kind === k.key}
              onClick={() => setKind(k.key)}
            >
              {k.label} <span className="ocl-filter__count">{count(k.key)}</span>
            </button>
          ))}
        </div>
      )}

      {view !== "cards" ? (
        <Timeline venues={shown} mode={view === "lookback" ? "events" : "deadlines"} />
      ) : (
        <div className="ocl-venues__list">
          {shown.map((venue) => (
            <VenueCard key={venue.id} venue={venue} />
          ))}
        </div>
      )}
    </div>
  );
}
