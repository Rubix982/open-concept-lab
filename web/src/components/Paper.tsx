import type { ReactNode } from "react";
import clsx from "clsx";

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
 */
export function Abstract({
  keywords,
  children,
}: {
  keywords?: string[];
  children: ReactNode;
}): ReactNode {
  return (
    <section className="ocl-abstract" aria-label="Abstract">
      <div className="ocl-abstract__label">Abstract</div>
      {children}
      {keywords?.length ? (
        <p className="ocl-abstract__kw">
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
