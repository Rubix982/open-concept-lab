import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Project } from "@site/plugins/lab-data";
import Stage from "@site/src/components/writing/Stage";

/**
 * The research projects, on a page of their own.
 *
 * The notebook index lists every project, research or not, and reaches each
 * one's pages through the docs sidebar. This page keeps to the projects marked
 * `kind: research` in data/projects.yml and adds what a reader outside the work
 * needs next: where the code is and how much of the reading list it rests on.
 * Same `ocl-garden` shell and card as the notebook and writing indexes.
 */

/** "28 Nov 2026" */
function shortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

function ResearchCard({ project, papers }: { project: Project; papers: number }): ReactNode {
  const art = useBaseUrl(`/img/art/projects/${project.name}.svg`);
  return (
    <article className="ocl-garden__card">
      <Link to={project.notebook} className="ocl-garden__link">
        <span className="ocl-garden__picture">
          <img src={art} alt="" loading="lazy" decoding="async" />
        </span>
        <span className="ocl-garden__body">
          <span className="ocl-garden__title">{project.name}</span>
          <span className="ocl-garden__summary">{project.what}</span>
          <span className="ocl-garden__meta" title={project.phaseDetail}>
            <Stage status={project.tone} label={false} />
            <span>{project.phase}</span>
            {project.updated ? <span>Plan updated {shortDate(project.updated)}</span> : null}
          </span>
        </span>
      </Link>
      <p className="ocl-garden__pages">
        <Link to={project.notebook}>Notebook page</Link>
        <a href={project.repo} target="_blank" rel="noreferrer">
          Code ↗
        </a>
        {papers > 0 ? (
          <Link to="/reading">
            {papers} {papers === 1 ? "paper" : "papers"} in Reading
          </Link>
        ) : null}
      </p>
    </article>
  );
}

export default function Research(): ReactNode {
  const { projects, papers } = usePluginData("ocl-lab-data") as LabData;
  const research = projects.filter((p) => p.kind === "research");
  const fieldArt = useBaseUrl("/img/art/pages/mech-interp-2026.svg");

  return (
    <Layout
      title="Research"
      description="The research projects: what each is trying to establish, where it stands, its notebook page and its code."
    >
      <main className="ocl-page ocl-research">
        <div className="ocl-index ocl-garden">
          <header className="ocl-garden__head">
            <p className="ocl-garden__count" aria-label={`${research.length} research projects`}>
              {research.length}
            </p>
            <h1 className="ocl-garden__heading">Research</h1>
            <p className="ocl-garden__lede">
              Most of it asks how far an edit to one fact in a language model
              spreads to other facts. The objective and phase on each card are
              read from that project's own plan. The working state is on its{" "}
              <Link to="/notebook">notebook</Link> page, and dated pieces are in{" "}
              <Link to="/writing">writing</Link>.
            </p>
          </header>

          <div className="ocl-garden__grid">
            {research.map((project) => (
              <ResearchCard
                key={project.name}
                project={project}
                papers={papers.filter((p) => p.projects.includes(project.name)).length}
              />
            ))}
          </div>

          <section className="ocl-garden__desk" aria-label="Around the research">
            <h2 className="ocl-garden__deskTitle">Around the research</h2>
            <div className="ocl-garden__grid">
              <article className="ocl-garden__card">
                <Link to="/notebook/mech-interp-2026" className="ocl-garden__link">
                  <span className="ocl-garden__picture">
                    <img src={fieldArt} alt="" loading="lazy" decoding="async" />
                  </span>
                  <span className="ocl-garden__body">
                    <span className="ocl-garden__title">The field in 2026</span>
                    <span className="ocl-garden__summary">
                      Where work on model internals was judged this year, what each
                      venue asked for, and which of those asks nothing here answers.
                    </span>
                  </span>
                </Link>
              </article>
            </div>
          </section>
        </div>
      </main>
    </Layout>
  );
}
