import { useState, type ReactNode } from "react";
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

function VenueCard({ venue }: { venue: Venue }): ReactNode {
  return (
    <article className="ocl-venue">
      <header className="ocl-venue__head">
        <h3 className="ocl-venue__name">
          {venue.url ? (
            <a href={venue.url} target="_blank" rel="noreferrer">
              {venue.name}
            </a>
          ) : (
            venue.name
          )}
        </h3>
        <span className="ocl-venue__series">{venue.series}</span>
      </header>

      {venue.due ? <p className="ocl-venue__due">Due {venue.due}</p> : null}

      <p className="ocl-venue__when">
        {venue.when}
        {venue.where ? ` · ${venue.where}` : ""}
      </p>

      <p className="ocl-venue__asks">{venue.asks}</p>

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
    </article>
  );
}

export default function Venues({ year = 2026 }: { year?: number }): ReactNode {
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

      <div className="ocl-venues__list">
        {shown.map((venue) => (
          <VenueCard key={venue.id} venue={venue} />
        ))}
      </div>
    </div>
  );
}
