import { Fragment, useEffect, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Paper } from "@site/plugins/lab-data";
import PageArt from "@site/src/components/PageArt";

/** Author strings end in an initial's period; don't double it up. */
function authorLine(authors: string, venue?: string): string {
  const trimmed = authors.replace(/\.\s*$/, "");
  return venue ? `${trimmed}. ${venue}` : trimmed;
}

function Pill({ tone, children }: { tone: string; children: ReactNode }): ReactNode {
  return <span className={`ocl-pill ocl-pill--${tone}`}>{children}</span>;
}

function PaperRow({ paper }: { paper: Paper }): ReactNode {
  return (
    <tr id={paper.id}>
      <td className="ocl-table__main">
        {paper.url ? (
          <a href={paper.url} target="_blank" rel="noreferrer">
            {paper.title}
          </a>
        ) : (
          paper.title
        )}
        <span className="ocl-table__sub">
          {authorLine(paper.authors, paper.venue)}
        </span>
        {paper.gives_me ? (
          <span className="ocl-table__note">{paper.gives_me}</span>
        ) : null}
      </td>
      <td className="ocl-table__num">{paper.year}</td>
      <td>
        <Pill tone={paper.status}>{paper.status.replace("-", " ")}</Pill>
      </td>
      <td>
        <Pill tone={`rel-${paper.relevance}`}>{paper.relevance}</Pill>
      </td>
      <td className="ocl-table__projects">
        {paper.projects.map((project, i) => (
          <span key={project}>
            {i > 0 ? ", " : ""}
            <Link to={`/notebook/${project}/`}>{project}</Link>
          </span>
        ))}
      </td>
      <td>
        {paper.verified ? (
          <span className="ocl-check" title="Venue and year checked against the paper">
            checked
          </span>
        ) : (
          <span className="ocl-check ocl-check--no" title="From a secondhand note — do not cite from this entry yet">
            unchecked
          </span>
        )}
      </td>
    </tr>
  );
}

const fieldOf = (p: Paper) => p.field ?? "Other";
const areaOf = (p: Paper) => p.area ?? "Other";

/** Papers grouped by a key, groups in the order of their most relevant paper. */
function groupBy(list: Paper[], key: (p: Paper) => string): [string, Paper[]][] {
  const groups = new Map<string, Paper[]>();
  for (const paper of list) groups.set(key(paper), [...(groups.get(key(paper)) ?? []), paper]);
  return [...groups.entries()];
}

function LedgerRows({ list }: { list: Paper[] }): ReactNode {
  return groupBy(list, (p) => `${fieldOf(p)} · ${areaOf(p)}`).map(([label, group]) => (
    <Fragment key={label}>
      <tr className="ocl-table__group">
        <th colSpan={6} scope="colgroup">{label}</th>
      </tr>
      {group.map((paper) => (
        <PaperRow key={paper.id} paper={paper} />
      ))}
    </Fragment>
  ));
}

/** A stable colour for a paper, from its id, so a cover never changes between builds. */
function hue(id: string): number {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (h % 6) + 1;
}

/** Surnames only, the way a spine lists them. */
function surnames(authors: string): string {
  // An organisation ("Prime Intellect Team") has no initials; keep it whole.
  if (!/,\s*[A-Z]\./.test(authors)) return authors.trim();
  // Drop the initials ("J.", "J.-M.", "et al."), keep every surname, short ones like Li and He included.
  const names = authors
    .split(/,\s*/)
    .map((n) => n.replace(/^&\s*/, "").trim())
    .filter((n) => n && !/^([A-Z]\.\s?-?\s?)+$/.test(n) && n !== "et al.");
  const last = names.map((n) => n.trim().split(/\s+/)[0].replace(/,$/, ""));
  if (last.length <= 2) return last.join(" & ");
  return `${last[0]} et al.`;
}

const STATUS_LABEL: Record<string, string> = {
  read: "Read",
  skimmed: "Skimmed",
  "to-read": "To read",
};

/**
 * A paper as a cover on a shelf: a coloured jacket, its venue and year in the
 * band at the top, the title set large, the authors at the foot. Read papers
 * carry a tick; secondhand ones a corner fold that says not to cite them yet.
 */
function PaperCover({ paper, onOpenRow }: { paper: Paper; onOpenRow: (id: string) => void }): ReactNode {
  const body = (
    <>
      <span className="ocl-shelf__band">
        <span>{paper.venue ?? "Preprint"}</span>
        <span>{paper.year}</span>
      </span>
      <span className="ocl-shelf__title">{paper.title}</span>
      <span className="ocl-shelf__authors">{surnames(paper.authors)}</span>
      <span className={`ocl-shelf__status ocl-shelf__status--${paper.status}`}>
        {paper.status === "read" ? "✓ " : null}
        {STATUS_LABEL[paper.status] ?? paper.status}
      </span>
      {!paper.verified ? <span className="ocl-shelf__fold" title="Secondhand: not citable yet" /> : null}
    </>
  );
  const className = `ocl-shelf__cover ocl-shelf__cover--${hue(paper.id)} ocl-shelf__cover--rel-${paper.relevance}`;
  return paper.url ? (
    <a className={className} href={paper.url} target="_blank" rel="noreferrer" title={paper.gives_me ?? paper.title}>
      {body}
    </a>
  ) : (
    <a
      className={className}
      href={`#${paper.id}`}
      title={paper.gives_me ?? paper.title}
      onClick={(e) => {
        e.preventDefault();
        onOpenRow(paper.id);
      }}
    >
      {body}
    </a>
  );
}

type StatusFilter = "all" | "read" | "skimmed" | "to-read";
type CheckFilter = "all" | "checked" | "unchecked";
type Filters = { q: string; field: string | null; area: string | null; status: StatusFilter; check: CheckFilter };

const NO_FILTERS: Filters = { q: "", field: null, area: null, status: "all", check: "all" };
/** Covers shown per area before "Show all": about one row at full width. */
const SHELF_PREVIEW = 6;

/** `ignore` drops one level, so a chip's count says what clicking it would show. */
function matches(paper: Paper, f: Filters, ignore: "none" | "field" | "area" = "none"): boolean {
  if (ignore !== "field" && f.field && fieldOf(paper) !== f.field) return false;
  if (ignore === "none" && f.area && areaOf(paper) !== f.area) return false;
  if (f.status !== "all" && paper.status !== f.status) return false;
  if (f.check === "checked" && !paper.verified) return false;
  if (f.check === "unchecked" && paper.verified) return false;
  const q = f.q.trim().toLowerCase();
  if (!q) return true;
  return [paper.title, paper.authors, paper.venue, paper.gives_me, paper.field, paper.area, String(paper.year)]
    .some((field) => field?.toLowerCase().includes(q));
}

function isFiltered(f: Filters): boolean {
  return f.q.trim() !== "" || f.field !== null || f.area !== null || f.status !== "all" || f.check !== "all";
}

/** Filters live in the query string, so a filtered view can be linked to. */
function readFilters(): Filters {
  const params = new URLSearchParams(window.location.search);
  const status = params.get("status");
  const check = params.get("check");
  return {
    q: params.get("q") ?? "",
    field: params.get("field"),
    area: params.get("area"),
    status: status === "read" || status === "skimmed" || status === "to-read" ? status : "all",
    check: check === "checked" || check === "unchecked" ? check : "all",
  };
}

function writeFilters(f: Filters): void {
  const params = new URLSearchParams();
  if (f.q.trim()) params.set("q", f.q.trim());
  if (f.field) params.set("field", f.field);
  if (f.area) params.set("area", f.area);
  if (f.status !== "all") params.set("status", f.status);
  if (f.check !== "all") params.set("check", f.check);
  const search = params.toString();
  history.replaceState(null, "", `${window.location.pathname}${search ? `?${search}` : ""}${window.location.hash}`);
}

function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: [T, string][];
  onChange: (v: T) => void;
}): ReactNode {
  return (
    <div className="ocl-filter__segment ocl-voices__switch" role="group" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" aria-pressed={value === v} onClick={() => onChange(v)}>
          {text}
        </button>
      ))}
    </div>
  );
}

function FilterBar({
  papers,
  filters,
  setFilters,
  shown,
}: {
  papers: Paper[];
  filters: Filters;
  setFilters: (f: Filters) => void;
  shown: number;
}): ReactNode {
  const fields = groupBy(papers, fieldOf).map(([field]) => ({
    field,
    n: papers.filter((p) => fieldOf(p) === field && matches(p, filters, "field")).length,
  }));
  // Sub-areas appear once a field is chosen; with one sub-area there is nothing to choose.
  const areas = filters.field
    ? groupBy(papers.filter((p) => fieldOf(p) === filters.field), areaOf).map(([area]) => ({
        area,
        n: papers.filter((p) => areaOf(p) === area && matches(p, filters, "area")).length,
      }))
    : [];
  const set = (patch: Partial<Filters>) => setFilters({ ...filters, ...patch });
  return (
    <div className="ocl-filter" role="search">
      <div className="ocl-filter__row">
        <input
          className="ocl-filter__search"
          type="search"
          placeholder="Filter by title, author, venue, or note"
          aria-label="Filter papers"
          value={filters.q}
          onChange={(e) => set({ q: e.target.value })}
        />
        <Segmented<StatusFilter>
          label="Status"
          value={filters.status}
          onChange={(status) => set({ status })}
          options={[["all", "Any status"], ["read", "Read"], ["skimmed", "Skimmed"], ["to-read", "To read"]]}
        />
        <Segmented<CheckFilter>
          label="Citation"
          value={filters.check}
          onChange={(check) => set({ check })}
          options={[["all", "Any citation"], ["checked", "Checked"], ["unchecked", "Unchecked"]]}
        />
      </div>
      <div className="ocl-filter__areas" role="group" aria-label="Field">
        <button
          type="button"
          className="ocl-filter__chip"
          aria-pressed={filters.field === null}
          onClick={() => set({ field: null, area: null })}
        >
          All fields
        </button>
        {fields.map(({ field, n }) => (
          <button
            key={field}
            type="button"
            className="ocl-filter__chip"
            aria-pressed={filters.field === field}
            disabled={n === 0 && filters.field !== field}
            onClick={() => set({ field: filters.field === field ? null : field, area: null })}
          >
            {field} <span>{n}</span>
          </button>
        ))}
      </div>
      {areas.length > 1 ? (
        <div className="ocl-filter__areas ocl-filter__areas--sub" role="group" aria-label="Area within the field">
          <button
            type="button"
            className="ocl-filter__chip"
            aria-pressed={filters.area === null}
            onClick={() => set({ area: null })}
          >
            All of {filters.field}
          </button>
          {areas.map(({ area, n }) => (
            <button
              key={area}
              type="button"
              className="ocl-filter__chip"
              aria-pressed={filters.area === area}
              disabled={n === 0 && filters.area !== area}
              onClick={() => set({ area: filters.area === area ? null : area })}
            >
              {area} <span>{n}</span>
            </button>
          ))}
        </div>
      ) : null}
      <p className="ocl-filter__count" aria-live="polite">
        {isFiltered(filters) ? (
          <>
            Showing {shown} of {papers.length}.{" "}
            <button type="button" className="ocl-filter__clear" onClick={() => setFilters(NO_FILTERS)}>
              Clear filters
            </button>
          </>
        ) : (
          <>
            {papers.length} papers in {fields.length} fields and {groupBy(papers, (p) => `${fieldOf(p)}/${areaOf(p)}`).length} areas.
          </>
        )}
      </p>
    </div>
  );
}

function ShelfArea({
  area,
  group,
  showAll,
  onOpenRow,
}: {
  area: string;
  group: Paper[];
  showAll: boolean;
  onOpenRow: (id: string) => void;
}): ReactNode {
  const [open, setOpen] = useState(false);
  const expanded = showAll || open;
  const visible = expanded ? group : group.slice(0, SHELF_PREVIEW);
  const hidden = group.length - SHELF_PREVIEW;
  return (
    <div className="ocl-shelf__area">
      <h4 className="ocl-shelf__areaTitle">
        {area} <span>{group.length}</span>
      </h4>
      <div className="ocl-shelf__grid">
        {visible.map((paper) => (
          <PaperCover key={paper.id} paper={paper} onOpenRow={onOpenRow} />
        ))}
      </div>
      {!showAll && hidden > 0 ? (
        <button type="button" className="ocl-shelf__more" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "Show fewer" : `Show all ${group.length}`}
        </button>
      ) : null}
    </div>
  );
}

export default function Reading(): ReactNode {
  const { papers } = usePluginData("ocl-lab-data") as LabData;

  const count = (predicate: (p: Paper) => boolean) =>
    papers.filter(predicate).length;

  const unverifiedAll = papers.filter((p) => !p.verified);
  const [view, setView] = useState<"shelf" | "ledger">("shelf");
  const [filters, setFiltersState] = useState<Filters>(NO_FILTERS);
  const setFilters = (f: Filters) => {
    setFiltersState(f);
    writeFilters(f);
  };
  useEffect(() => setFiltersState(readFilters()), []);

  const filtered = papers.filter((p) => matches(p, filters));
  const verified = filtered.filter((p) => p.verified);
  const unverified = filtered.filter((p) => !p.verified);
  const narrowed = isFiltered(filters);

  // A link to a paper's row (/reading#id, as <Cite> makes) opens the ledger on it.
  const openRow = (id: string) => {
    setView("ledger");
    requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ block: "center" });
      history.replaceState(null, "", `#${id}`);
    });
  };
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (id && papers.some((p) => p.id === id)) openRow(id);
  }, []);

  return (
    <Layout
      title="Reading"
      description="What I have read, skimmed, and still need to read — with which entries have been checked against the paper."
    >
      <main className="ocl-page">
        <header className="ocl-page__head ocl-page__head--art">
          <PageArt name="reading" />
          <h1 className="ocl-page__title">Reading</h1>
          <p className="ocl-page__lede">
            The papers my current work rests on, ordered by how much they bear
            on it. The last column says whether I have checked the venue and
            year against the paper itself — an unchecked entry came from a
            secondhand note and should not be cited from here.
          </p>
          <dl className="ocl-tally">
            <div>
              <dt>Papers</dt>
              <dd>{papers.length}</dd>
            </div>
            <div>
              <dt>Read</dt>
              <dd>{count((p) => p.status === "read")}</dd>
            </div>
            <div>
              <dt>Skimmed</dt>
              <dd>{count((p) => p.status === "skimmed")}</dd>
            </div>
            <div>
              <dt>To read</dt>
              <dd>{count((p) => p.status === "to-read")}</dd>
            </div>
            <div>
              <dt>Unchecked</dt>
              <dd className={unverifiedAll.length > 0 ? "ocl-tally--flag" : undefined}>
                {unverifiedAll.length}
              </dd>
            </div>
          </dl>
        </header>

        <div className="ocl-shelf__switch ocl-voices__switch" role="group" aria-label="View">
          <button type="button" aria-pressed={view === "shelf"} onClick={() => setView("shelf")}>
            Shelf
          </button>
          <button type="button" aria-pressed={view === "ledger"} onClick={() => setView("ledger")}>
            Ledger
          </button>
        </div>

        <FilterBar papers={papers} filters={filters} setFilters={setFilters} shown={filtered.length} />

        {filtered.length === 0 ? (
          <p className="ocl-page__note ocl-filter__empty">
            No papers match.{" "}
            <button type="button" className="ocl-filter__clear" onClick={() => setFilters(NO_FILTERS)}>
              Clear filters
            </button>
          </p>
        ) : null}

        {view === "shelf" && filtered.length > 0 ? (
          <section className="ocl-page__section ocl-shelf" aria-label="Papers as a shelf">
            <p className="ocl-page__note">
              Grouped by field and area, and ordered within each by how much it bears on the work. A folded corner marks
              a secondhand entry, not citable yet. Open a cover for the paper.
            </p>
            {groupBy(filtered, fieldOf).map(([field, inField]) => (
              <div key={field} className="ocl-shelf__field">
                <h3 className="ocl-shelf__fieldTitle">
                  {field} <span>{inField.length}</span>
                </h3>
                {groupBy(inField, areaOf).map(([area, group]) => (
                  <ShelfArea key={area} area={area} group={group} showAll={narrowed} onOpenRow={openRow} />
                ))}
              </div>
            ))}
          </section>
        ) : null}

        {view === "ledger" ? (<>
        {verified.length > 0 ? (
        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">Checked against the paper</h2>
          <div className="ocl-table__scroll">
            <table className="ocl-table">
              <thead>
                <tr>
                  <th>Paper</th>
                  <th className="ocl-table__num">Year</th>
                  <th>Status</th>
                  <th>Bearing</th>
                  <th>Project</th>
                  <th>Citation</th>
                </tr>
              </thead>
              <tbody>
                <LedgerRows list={verified} />
              </tbody>
            </table>
          </div>
        </section>
        ) : null}

        {unverified.length > 0 ? (
          <section className="ocl-page__section">
            <h2 className="ocl-page__sectionTitle">Secondhand — not citable yet</h2>
            <p className="ocl-page__note">
              These came from a literature map or an abstract. Reading one and
              checking its venue moves it up into the table above; several are
              blocking work, which is the point of keeping them visible.
            </p>
            <div className="ocl-table__scroll">
              <table className="ocl-table">
                <thead>
                  <tr>
                    <th>Paper</th>
                    <th className="ocl-table__num">Year</th>
                    <th>Status</th>
                    <th>Bearing</th>
                    <th>Project</th>
                    <th>Citation</th>
                  </tr>
                </thead>
                <tbody>
                  <LedgerRows list={unverified} />
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
        </>) : null}

        <p className="ocl-page__foot">
          Kept in <code>data/papers.yml</code>. In any piece, <code>{'<Cite id="cohen2024ripple" />'}</code>{" "}
          resolves to the entry.
        </p>
      </main>
    </Layout>
  );
}
