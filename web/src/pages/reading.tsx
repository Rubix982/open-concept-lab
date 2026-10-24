import { useEffect, useState, type ReactNode } from "react";
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

/** A stable colour for a paper, from its id, so a cover never changes between builds. */
function hue(id: string): number {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (h % 6) + 1;
}

/** Surnames only, the way a spine lists them. */
function surnames(authors: string): string {
  const names = authors.split(/,\s*(?=[A-Z][^,]*\.)|,\s*/).filter((n) => /[a-z]{2}/.test(n));
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

export default function Reading(): ReactNode {
  const { papers } = usePluginData("ocl-lab-data") as LabData;

  const count = (predicate: (p: Paper) => boolean) =>
    papers.filter(predicate).length;

  const verified = papers.filter((p) => p.verified);
  const unverified = papers.filter((p) => !p.verified);
  const [view, setView] = useState<"shelf" | "ledger">("shelf");

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
              <dd className={unverified.length > 0 ? "ocl-tally--flag" : undefined}>
                {unverified.length}
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

        {view === "shelf" ? (
          <section className="ocl-page__section ocl-shelf" aria-label="Papers as a shelf">
            <p className="ocl-page__note">
              Ordered by how much each bears on the work. A folded corner marks
              a secondhand entry, not citable yet. Open a cover for the paper.
            </p>
            <div className="ocl-shelf__grid">
              {papers.map((paper) => (
                <PaperCover key={paper.id} paper={paper} onOpenRow={openRow} />
              ))}
            </div>
          </section>
        ) : null}

        {view === "ledger" ? (<>
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
                {verified.map((paper) => (
                  <PaperRow key={paper.id} paper={paper} />
                ))}
              </tbody>
            </table>
          </div>
        </section>

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
                  {unverified.map((paper) => (
                    <PaperRow key={paper.id} paper={paper} />
                  ))}
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
