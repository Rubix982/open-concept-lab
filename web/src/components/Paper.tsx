import { Children, cloneElement, isValidElement } from "react";
import type { ReactElement, ReactNode } from "react";
import clsx from "clsx";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { PaperSwitch } from "./LabLog";

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
export function Prov({
  id,
  to,
  detail,
}: {
  id: string;
  to?: string;
  /** The run's one-line description. Filled in by `plugins/remark-paper-refs.mjs`
      from the provenance row itself, so it cannot disagree with the table. */
  detail?: string;
}): ReactNode {
  /* The row, not the top of the table. Landing on `#runs` left the reader to
     find their own id among forty, which is the work the marker exists to
     save. `Run` already gives every row a `run-<id>` anchor; the ids here are
     typed with a non-breaking hyphen so they never wrap, and that character is
     not the one in the anchor. */
  const anchor = id.replace(/[\u2010\u2011\u2012\u2013]/g, "-");
  const tip = detail ? `${anchor} — ${detail}` : `${anchor} — see the provenance table`;
  return (
    <a
      className="ocl-prov"
      href={to ?? `#run-${anchor}`}
      data-tip={tip}
      aria-label={tip}
    >
      [{id}]
    </a>
  );
}

/* ------------------------------------------------------------------ */
/* Findings ledger                                                     */
/* ------------------------------------------------------------------ */

/**
 * A claim's fate. `narrowed` is not a softer `withdrawn`: the claim survives in a
 * weaker form, so the row is not struck through and the weaker form is what the
 * row states. The other three are retired and the text is struck.
 */
export type FindingStatus =
  | "standing"
  | "narrowed"
  | "withdrawn"
  | "superseded"
  | "denied";

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
  /* A narrowed claim is still a claim, so it is not struck through — but it is
     not standing either, and reading it as standing is the mistake the column
     exists to prevent. */
  const retired = status !== "standing" && status !== "narrowed";
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
        <span
          className={clsx({
            "ocl-ok": status === "standing",
            "ocl-partial": status === "narrowed",
            "ocl-no": retired,
          })}
        >
          {status}
        </span>
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
  /* One ticket can write more than one row — a run that swept three models
     wrote a file per model — and until 18 November 2026 each of those rows
     carried the same `run-<id>` anchor. Duplicate ids are invalid, and a
     browser resolves them by going to the first, so the second row could not
     be linked at all. Numbering repeats here, where the rows are in one place,
     is the same thing a slugger does to two identical headings: the first keeps
     the plain anchor, so every reference written as [E-004] still lands on it. */
  const seen = new Map<string, number>();
  const rows = Children.map(children, (child) => {
    if (!isValidElement(child)) return child;
    const el = child as ReactElement<{ id?: string; occurrence?: number }>;
    const id = el.props?.id;
    if (typeof id !== "string") return child;
    const n = (seen.get(id) ?? 0) + 1;
    seen.set(id, n);
    return n === 1 ? child : cloneElement(el, { occurrence: n });
  });
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
        <tbody>{rows}</tbody>
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
  occurrence,
  children,
}: {
  id: string;
  model: string;
  n: ReactNode;
  date: string;
  /** What the run wrote, relative to results/. */
  out: string;
  /** Set by `Runs` on the second and later rows sharing one id. */
  occurrence?: number;
  children: ReactNode;
}): ReactNode {
  // A committed file is linked; a per-run directory is not, because those were
  // never committed and most no longer exist. Naming a row as gone is worth
  // more than a link that 404s, and more than a filename a reader cannot tell
  // is unreachable.
  const base =
    "https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/results/";
  // Space-separated, because a run that swept three models wrote three files
  // and naming one of them would be a quieter kind of wrong than naming none.
  const files = out.split(" ").filter((o) => o.endsWith(".json"));
  /* The id is typeset with a non-breaking hyphen so it never wraps mid-token.
     That character is not the one anybody types in a link, so the anchor is
     normalised to ASCII while the cell keeps the typeset form. */
  const anchor =
    id.replace(/[\u2010\u2011\u2012\u2013]/g, "-") + (occurrence ? `-${occurrence}` : "");
  return (
    <tr id={`run-${anchor}`}>
      <td className="n">{id}</td>
      <td>{children}</td>
      <td className="n">{model}</td>
      <td className="n">{n}</td>
      <td className="n">{date}</td>
      <td className="n">
        {files.length ? (
          files.map((f, i) => (
            <span key={f}>
              {i > 0 ? <br /> : null}
              <a href={base + f}>{f}</a>
            </span>
          ))
        ) : (
          <span className="ocl-run__gone" title="A per-run directory: never committed, and no longer on disk">
            {out}
          </span>
        )}
      </td>
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
  /** true when a sibling lab-log page exists; shows the Paper / Lab log switch. */
  log?: boolean;
  keywords?: string[];
  contributions?: string[];
  reading_guide?: string;
  /** What it costs a reader, e.g. "55-minute read". An estimate, stated so
      nobody has to discover the length by scrolling. */
  reading?: string;
  index?: { label: string; what: string }[];
  /** One picture carrying the result, shown before the abstract. */
  hero?: { src: string; alt: string };
  /** The page in four or five parts, each shown with figures drawn from it. */
  parts?: { n: string; title: string; what: string; href: string; figs?: string[] }[];
  /** Set once `scripts/paper_pdf.py` has written static/pdf/<project>.pdf. */
  pdf?: boolean;
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

  /* The site is served under a base path. A raw href misses it and lands on a
     404 that looks like a working link, which is the same fault <Figure> had
     with its src. useBaseUrl leaves absolute URLs alone. */
  const buildsOn = useBaseUrl(e.builds_on?.href ?? "");
  /* One hook, not one per thumbnail: a hook inside the parts loop would run a
     different number of times whenever the list changes. */
  const base = useBaseUrl("/").replace(/\/$/, "");
  const project = metadata.id.split("/")[0];
  const pdf = useBaseUrl(`/pdf/${project}.pdf`);

  const stamp = [e.kind, e.id, e.version].filter(Boolean).join(" · ");
  const hasMeta = e.started || e.updated || e.builds_on;

  return (
    <>
      <header className="ocl-paperhead">
        {e.log ? <PaperSwitch /> : null}
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
            {e.reading ? <span>{e.reading}</span> : null}
            {e.builds_on ? (
              <span>
                Builds on <a href={buildsOn}>{e.builds_on.label}</a>
              </span>
            ) : null}
            {e.pdf ? (
              <span>
                <a href={pdf}>PDF</a>, two columns
              </span>
            ) : null}
          </div>
        ) : null}
      </header>

      {e.hero ? (
        <div className="ocl-hero">
          <img src={base + e.hero.src} alt={e.hero.alt} />
        </div>
      ) : null}

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

      {e.parts?.length ? (
        <nav className="ocl-parts" aria-label="What is in this paper">
          <div className="ocl-parts__label">What is in here</div>
          <ol>
            {e.parts.map((part) => (
              <li key={part.href}>
                <a href={part.href}>
                  {part.figs?.length ? (
                    <span className="ocl-parts__figs" aria-hidden="true">
                      {part.figs.map((f) => (
                        <img key={f} src={base + f} alt="" loading="lazy" />
                      ))}
                    </span>
                  ) : null}
                  <span className="ocl-parts__n">{part.n}</span>
                  <span className="ocl-parts__title">{part.title}</span>
                </a>
                <p className="ocl-parts__what">{part.what}</p>
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
    </>
  );
}

/**
 * One plain-English line under a section heading, saying what is in the
 * section. It describes the contents; it never argues that they are good.
 *
 * The headings on this paper are claims, which is right for a paper and hard
 * on a first-time reader — a claim-shaped heading tells you the verdict before
 * you have the vocabulary to read it. This line carries the vocabulary.
 */
export function Gist({ children }: { children: ReactNode }): ReactNode {
  return <p className="ocl-gist">{children}</p>;
}
