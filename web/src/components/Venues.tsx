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
  { key: "workshop", label: "Workshops" },
  { key: "competition", label: "Competitions" },
  { key: "funding", label: "Funding" },
];

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

export default function Venues(): ReactNode {
  const { venues } = usePluginData("ocl-lab-data") as LabData;
  const [kind, setKind] = useState<Venue["kind"] | "all">("all");

  const shown = kind === "all" ? venues : venues.filter((v) => v.kind === kind);
  const count = (k: Venue["kind"] | "all") =>
    k === "all" ? venues.length : venues.filter((v) => v.kind === k).length;

  return (
    <div className="ocl-venues">
      <div className="ocl-filter__areas" role="group" aria-label="Kind of venue">
        {KINDS.map((k) => (
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
