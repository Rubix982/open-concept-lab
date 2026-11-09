import type { ReactNode } from "react";
import clsx from "clsx";
import { useDoc } from "@docusaurus/plugin-content-docs/client";

/**
 * Paper mode.
 *
 * A notebook page opts in by putting <PaperHead> at the top. Everything after
 * it is a sibling in the MDX output, so the stylesheet reaches the rest of the
 * page with `.ocl-paperhead ~ *` — no wrapper, which matters because wrapping
 * the body in a component hides the headings from the table of contents.
 *
 * What the mode changes is density and apparatus, not the palette: justified
 * prose at a smaller size, numbered sections, figures floated into the column,
 * bordered tables, numbered equations. The tokens are the site's own.
 *
 * There is deliberately no "cite this page" block and no place to put an email
 * address. See agents/documentor/tickets.md, D-008.
 */

export function PaperHead({
  kind = "Working paper",
  docId,
  version,
  title,
  author,
  affiliation,
  started,
  updated,
  buildsOn,
}: {
  /** What this document is. Shown in the identifier line. */
  kind?: string;
  /** This lab's own document number, e.g. "OCL-2026-07". Not a preprint id. */
  docId?: string;
  /** e.g. "v0.4" */
  version?: string;
  title: string;
  /** A name. Never an email address. */
  author: ReactNode;
  /** The lab and where it is. */
  affiliation?: ReactNode;
  /** When the work began, e.g. "30 Sep 2026". */
  started?: string;
  /** When this document last changed. */
  updated?: string;
  /** The project this one stands on, as a link. */
  buildsOn?: ReactNode;
}): ReactNode {
  const stamp = [kind, docId, version].filter(Boolean).join(" · ");

  return (
    <header className="ocl-paperhead">
      {stamp ? <div className="ocl-paperhead__id">{stamp}</div> : null}
      <h1 className="ocl-paperhead__title">{title}</h1>
      <div className="ocl-paperhead__author">{author}</div>
      {affiliation ? (
        <div className="ocl-paperhead__affil">{affiliation}</div>
      ) : null}
      {started || updated || buildsOn ? (
        <div className="ocl-paperhead__meta">
          {started ? (
            <span>
              Started <b>{started}</b>
            </span>
          ) : null}
          {updated ? (
            <span>
              Updated <b>{updated}</b>
            </span>
          ) : null}
          {buildsOn ? <span>Builds on {buildsOn}</span> : null}
        </div>
      ) : null}
    </header>
  );
}

/**
 * The abstract. Not a numbered section — a paper's abstract never is — so it
 * carries a letterspaced label instead of a heading, and stays out of the
 * table of contents.
 *
 * The class is `ocl-paper-abstract`, not `ocl-abstract`. That name was already
 * taken by the hand-written abstract on notebook/edit-slice/review, which has
 * its own panel, left rule and measure. Reusing it gave this component a
 * background nothing had asked for and quietly restyled that other page.
 */
export function Abstract({
  keywords,
  children,
}: {
  keywords?: string[];
  children: ReactNode;
}): ReactNode {
  return (
    <section className="ocl-paper-abstract" aria-label="Abstract">
      <div className="ocl-paper-abstract__label">Abstract</div>
      {children}
      {keywords?.length ? (
        <p className="ocl-paper-abstract__kw">
          <i>Keywords</i> — {keywords.join(", ")}
        </p>
      ) : null}
    </section>
  );
}

/**
 * What this document adds, numbered. A contributions list is the one place a
 * reader looks to decide whether to read on, and writing it is a check on the
 * work: a contribution that cannot be stated in a line is not one yet.
 */
export function Contributions({ children }: { children: ReactNode }): ReactNode {
  return (
    <section className="ocl-contrib" aria-label="Contributions">
      <div className="ocl-contrib__label">Contributions</div>
      {children}
    </section>
  );
}

/**
 * A numbered display equation. The number is a CSS counter, so equations
 * renumber themselves when you move one.
 */
export function Eq({
  gloss,
  children,
}: {
  /** A few words in plain language saying what the expression is for. */
  gloss?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-eq">
      <div className="ocl-eq__body">
        <div className="ocl-eq__expr">{children}</div>
        {gloss ? <span className="ocl-eq__gloss">{gloss}</span> : null}
      </div>
      <span className="ocl-eq__num" aria-hidden="true" />
    </div>
  );
}

/** A run-in lead, set bold at the head of a paragraph. */
export function Lead({ children }: { children: ReactNode }): ReactNode {
  return <strong className="ocl-lead">{children}</strong>;
}

/**
 * A pointer from a number in the prose to the run that produced it.
 * Renders as a small superscript ticket id linking to the provenance table.
 */
export function Prov({ id, to = "#runs" }: { id: string; to?: string }): ReactNode {
  return (
    <a className="ocl-prov" href={to} title={`Measured by ${id} — see the provenance table`}>
      [{id}]
    </a>
  );
}

/* ------------------------------------------------------------------ */
/* Findings ledger                                                     */
/* ------------------------------------------------------------------ */

export type FindingStatus = "standing" | "withdrawn" | "superseded" | "denied";

export function Ledger({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable">
      <table className="ocl-ledger">
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            <th>#</th>
            <th>Claim, and what would refute it</th>
            <th className="n">value</th>
            <th className="n">status</th>
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

/**
 * One row of the ledger. A row without a falsifier is not admitted — the
 * component says so in place of the missing text rather than rendering a
 * blank, so the omission is visible on the page.
 */
export function Finding({
  id,
  status,
  value,
  falsifier,
  children,
}: {
  id: string;
  status: FindingStatus;
  value?: ReactNode;
  falsifier?: ReactNode;
  children: ReactNode;
}): ReactNode {
  const retired = status !== "standing";
  return (
    <tr>
      <td className="n">{id}</td>
      <td className={clsx({ "ocl-struck": retired })}>
        {children}
        <span className="ocl-falsifier">
          {falsifier ?? <em>No falsifier stated. This row is not a finding yet.</em>}
        </span>
      </td>
      <td className="n">{value ?? "—"}</td>
      <td className="n">
        <span className={retired ? "ocl-no" : "ocl-ok"}>{status}</span>
      </td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/* Provenance                                                          */
/* ------------------------------------------------------------------ */

export function Runs({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable" id="runs">
      <table>
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            <th className="n">id</th>
            <th>what it measured</th>
            <th className="n">model</th>
            <th className="n">n</th>
            <th className="n">date</th>
            <th className="n">output</th>
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Run({
  id,
  model,
  n,
  date,
  out,
  children,
}: {
  id: string;
  model: string;
  n: ReactNode;
  date: string;
  /** The results directory the run wrote, relative to results/. */
  out: string;
  children: ReactNode;
}): ReactNode {
  return (
    <tr id={`run-${id}`}>
      <td className="n">{id}</td>
      <td>{children}</td>
      <td className="n">{model}</td>
      <td className="n">{n}</td>
      <td className="n">{date}</td>
      <td className="n">{out}</td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/* Revisions                                                           */
/* ------------------------------------------------------------------ */

export function Revisions({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable">
      <table>
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            <th className="n">date</th>
            <th className="n">ver</th>
            <th>what changed, and what it cost</th>
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Rev({
  date,
  version,
  children,
}: {
  date: string;
  version: string;
  children: ReactNode;
}): ReactNode {
  return (
    <tr>
      <td className="n">{date}</td>
      <td className="n">{version}</td>
      <td>{children}</td>
    </tr>
  );
}

/* ------------------------------------------------------------------ */
/* Readiness                                                           */
/* ------------------------------------------------------------------ */

export function Readiness({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable">
      <table>
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            <th className="n" aria-label="met" />
            <th>requirement</th>
            <th>state today</th>
            <th className="n">where</th>
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Check({
  met = false,
  need,
  where,
  children,
}: {
  met?: boolean;
  /** The requirement, in the venue's terms. */
  need: ReactNode;
  /** Where on this page the evidence is. */
  where?: ReactNode;
  /** What is true today. */
  children: ReactNode;
}): ReactNode {
  return (
    <tr>
      <td className="n">
        <span className={met ? "ocl-ok" : "ocl-no"} role="img" aria-label={met ? "met" : "not met"}>
          {met ? "✓" : "✗"}
        </span>
      </td>
      <td>{need}</td>
      <td>{children}</td>
      <td className="n">{where ?? "—"}</td>
    </tr>
  );
}

/** A plain bordered table for results, so MDX tables and these agree. */
export function Data({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable">
      <table>
        {caption ? <caption>{caption}</caption> : null}
        {children}
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Project overview                                                    */
/* ------------------------------------------------------------------ */

/**
 * A row of figures describing the state of a project, for an overview page.
 *
 * Big-number tiles earn their place only where the figures are the point, and
 * on a project overview they are: how much has been decided, how much is open,
 * and on what. They do not belong on the paper, where every number already
 * carries a run behind it.
 */
export function Glance({ children }: { children: ReactNode }): ReactNode {
  return <div className="ocl-glance">{children}</div>;
}

export function Stat({
  value,
  label,
  note,
}: {
  value: ReactNode;
  label: ReactNode;
  /** What the figure is of, in a few words. */
  note?: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-stat">
      <div className="ocl-stat__value">{value}</div>
      <div className="ocl-stat__label">{label}</div>
      {note ? <div className="ocl-stat__note">{note}</div> : null}
    </div>
  );
}

/** A question this project asked, and what closed it. */
export function Cards({
  caption,
  children,
}: {
  caption?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <div className="ocl-ptable">
      <table>
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            <th className="n">card</th>
            <th>the question, as it was written before the run</th>
            <th className="n">closed</th>
            <th className="n">on</th>
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Card({
  id,
  outcome,
  date,
  denied = false,
  children,
}: {
  id: string;
  /** One or two words: denied, identity, two routes. */
  outcome: ReactNode;
  date: string;
  /** Mark the row where the answer went against the project. */
  denied?: boolean;
  children: ReactNode;
}): ReactNode {
  return (
    <tr>
      <td className="n">{id}</td>
      <td>{children}</td>
      <td className="n">
        <span className={denied ? "ocl-no" : "ocl-ok"}>{outcome}</span>
      </td>
      <td className="n">{date}</td>
    </tr>
  );
}

/** An open question, carried in the project's thread ledger. */
export function Threads({ children }: { children: ReactNode }): ReactNode {
  return <dl className="ocl-threads">{children}</dl>;
}

export function Thread({
  id,
  status,
  children,
}: {
  id: string;
  status: "open" | "answered" | "narrowed" | "parked";
  children: ReactNode;
}): ReactNode {
  return (
    <div className={clsx("ocl-thread", `ocl-thread--${status}`)}>
      <dt>
        <span className="ocl-thread__id">{id}</span>
        <span className="ocl-thread__status">{status}</span>
      </dt>
      <dd>{children}</dd>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* The paper template                                                  */
/* ------------------------------------------------------------------ */

/**
 * The canonical section order. A paper page carries all eight, numbered, as
 * ordinary markdown headings — not as component output, because Docusaurus
 * builds the contents rail from the markdown syntax tree and a heading emitted
 * by a React component never reaches it. `scripts/check-papers.mjs` enforces
 * the order at build time instead.
 */
export const PAPER_SECTIONS = [
  "Introduction",
  "Related work",
  "Methods",
  "Implementation",
  "Results",
  "Findings and claims",
  "Limitations",
  "Conclusion",
] as const;

type PaperEntry = {
  kind?: string;
  id?: string;
  version?: string;
  author?: string;
  affiliation?: string;
  started?: string;
  updated?: string;
  builds_on?: { label: string; href: string };
  keywords?: string[];
  contributions?: string[];
  reading_guide?: string;
  index?: { label: string; what: string }[];
};

/**
 * One paper, filled from one entry.
 *
 * Everything that is the same on every paper — the identifier line, the title
 * block, the abstract's label, the keyword line, the contributions, the figure
 * index — is rendered here from the `paper:` key in the page's front matter.
 * The page writes `<Paper>` once, puts the abstract inside it, and then writes
 * its sections as ordinary markdown.
 *
 * It returns a fragment rather than a wrapper, deliberately: paper mode is
 * selected by `.markdown:has(> .ocl-paperhead)`, so the header has to stay a
 * direct child of the markdown container.
 */
export function Paper({ children }: { children: ReactNode }): ReactNode {
  const { frontMatter, metadata } = useDoc();
  const fm = frontMatter as Record<string, unknown>;
  const e = (fm.paper ?? {}) as PaperEntry;
  const title = (fm.title as string) ?? metadata.title;

  const stamp = [e.kind, e.id, e.version].filter(Boolean).join(" · ");
  const hasMeta = e.started || e.updated || e.builds_on;

  return (
    <>
      <header className="ocl-paperhead">
        {stamp ? <div className="ocl-paperhead__id">{stamp}</div> : null}
        <h1 className="ocl-paperhead__title">{title}</h1>
        {e.author ? <div className="ocl-paperhead__author">{e.author}</div> : null}
        {e.affiliation ? (
          <div className="ocl-paperhead__affil">{e.affiliation}</div>
        ) : null}
        {hasMeta ? (
          <div className="ocl-paperhead__meta">
            {e.started ? (
              <span>
                Started <b>{e.started}</b>
              </span>
            ) : null}
            {e.updated ? (
              <span>
                Updated <b>{e.updated}</b>
              </span>
            ) : null}
            {e.builds_on ? (
              <span>
                Builds on <a href={e.builds_on.href}>{e.builds_on.label}</a>
              </span>
            ) : null}
          </div>
        ) : null}
      </header>

      {e.reading_guide ? (
        <aside className="ocl-paper-guide">
          <span className="ocl-paper-guide__label">Before you start</span>
          {e.reading_guide}
        </aside>
      ) : null}

      <section className="ocl-paper-abstract" aria-label="Abstract">
        <div className="ocl-paper-abstract__label">Abstract</div>
        {children}
        {e.keywords?.length ? (
          <p className="ocl-paper-abstract__kw">
            <i>Keywords</i> — {e.keywords.join(", ")}
          </p>
        ) : null}
      </section>

      {e.contributions?.length ? (
        <section className="ocl-contrib" aria-label="Contributions">
          <div className="ocl-contrib__label">Contributions</div>
          <ol>
            {e.contributions.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ol>
        </section>
      ) : null}

      {e.index?.length ? (
        <div className="ocl-ptable ocl-paper-index">
          <table>
            <caption>
              Figures and tables, with the section each belongs to.
            </caption>
            <tbody>
              {e.index.map((row) => (
                <tr key={row.label}>
                  <td className="n">{row.label}</td>
                  <td>{row.what}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
