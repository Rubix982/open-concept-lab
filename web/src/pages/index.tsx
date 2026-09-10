import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Paper } from "@site/plugins/lab-data";

type Project = {
  name: string;
  what: string;
  phase: string;
  tone: "provisional" | "standing" | "draft";
  to: string;
};

const PROJECTS: Project[] = [
  {
    name: "edit-slice",
    what: "Whether a weight edit reaches the facts that were premises for it, or only the facts that follow from it.",
    phase: "Phase 0 — definitions",
    tone: "draft",
    to: "/notebook/edit-slice/",
  },
  {
    name: "rome-neighbors",
    what: "Whether representational geometry predicts how far an edit propagates, resolved by entailment hop.",
    phase: "Experiments running",
    tone: "provisional",
    to: "/notebook/rome-neighbors/",
  },
  {
    name: "claim-graph",
    what: "A knowledge graph whose nodes are extracted claims rather than papers.",
    phase: "Slice working",
    tone: "standing",
    to: "/notebook/claim-graph/",
  },
];

function shortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

function SectionHead({
  title,
  href,
  linkLabel,
}: {
  title: string;
  href: string;
  linkLabel: string;
}): ReactNode {
  return (
    <div className="ocl-home__sectionHead">
      <h2 className="ocl-home__sectionTitle">{title}</h2>
      <Link className="ocl-home__sectionLink" to={href}>
        {linkLabel}
      </Link>
    </div>
  );
}

export default function Home(): ReactNode {
  const { writing, papers, built } = usePluginData("ocl-lab-data") as LabData;

  const unchecked = papers.filter((p) => !p.verified);
  const nextUp = papers
    .filter((p: Paper) => p.status === "to-read" && p.relevance === "high")
    .slice(0, 3);

  return (
    <Layout
      title="Open Concept Lab"
      description="Experiments, writing, and interactive pages on knowledge editing and interpretability — what a model believes and how to tell whether a change took hold."
    >
      <div className="ocl-home">
        <header className="ocl-home__masthead">
          <h1 className="ocl-home__title">
            What a model believes, and how to tell when it changes.
          </h1>
          <p className="ocl-home__blurb">
            Experiments, writing, and interactive pages I built to understand
            something. Most of what is here is provisional and says so, and the
            reading list marks which citations I have actually checked.
          </p>
        </header>

        <section className="ocl-home__section">
          <SectionHead title="Projects" href="/notebook" linkLabel="Notebook" />
          <table className="ocl-table ocl-table--flush">
            <tbody>
              {PROJECTS.map((project) => (
                <tr key={project.name}>
                  <td className="ocl-table__key">
                    <Link to={project.to}>{project.name}</Link>
                  </td>
                  <td className="ocl-table__main">{project.what}</td>
                  <td className="ocl-table__right">
                    <span className={`ocl-status ocl-status--${project.tone}`}>
                      {project.phase}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="ocl-home__section">
          <SectionHead title="Writing" href="/writing" linkLabel="All writing" />
          {writing.slice(0, 5).map((entry) => (
            <article className="ocl-entry" key={entry.permalink}>
              <time className="ocl-entry__date" dateTime={entry.date}>
                {shortDate(entry.date)}
              </time>
              <div>
                <h3 className="ocl-entry__title">
                  <Link to={entry.permalink}>{entry.title}</Link>
                </h3>
                {entry.summary ? (
                  <p className="ocl-entry__summary">{entry.summary}</p>
                ) : null}
              </div>
            </article>
          ))}
          {writing.length === 0 ? (
            <p className="ocl-home__empty">
              Nothing published yet. Add a file to <code>blog/</code>.
            </p>
          ) : null}
        </section>

        <section className="ocl-home__section">
          <SectionHead title="Reading" href="/reading" linkLabel="Reading list" />
          <dl className="ocl-tally">
            <div>
              <dt>Papers</dt>
              <dd>{papers.length}</dd>
            </div>
            <div>
              <dt>Read</dt>
              <dd>{papers.filter((p) => p.status === "read").length}</dd>
            </div>
            <div>
              <dt>To read</dt>
              <dd>{papers.filter((p) => p.status === "to-read").length}</dd>
            </div>
            <div>
              <dt>Citations unchecked</dt>
              <dd className={unchecked.length > 0 ? "ocl-tally--flag" : undefined}>
                {unchecked.length}
              </dd>
            </div>
          </dl>
          {nextUp.length > 0 ? (
            <table className="ocl-table ocl-table--flush">
              <tbody>
                {nextUp.map((paper) => (
                  <tr key={paper.id}>
                    <td className="ocl-table__main">
                      <Link to={`/reading#${paper.id}`}>{paper.title}</Link>
                      {paper.gives_me ? (
                        <span className="ocl-table__sub">{paper.gives_me}</span>
                      ) : null}
                    </td>
                    <td className="ocl-table__right">
                      <span className="ocl-pill ocl-pill--to-read">next up</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>

        <section className="ocl-home__section">
          <SectionHead title="Built" href="/built" linkLabel="All pages" />
          <table className="ocl-table ocl-table--flush">
            <tbody>
              {built.slice(0, 6).map((page) => (
                <tr key={page.name}>
                  <td className="ocl-table__key">{page.topic}</td>
                  <td className="ocl-table__main">
                    <Link to="/built">{page.title}</Link>
                    <span className="ocl-table__sub">{page.what}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </Layout>
  );
}
