import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Project, Writeup } from "@site/plugins/lab-data";
import Stage from "@site/src/components/writing/Stage";
import { withWriteup, writeupMeta } from "@site/src/components/Projects";

/**
 * Research: the overall write-up of each project that has one.
 *
 * The notebook holds the experiments; this page holds what they add up to. A
 * write-up is named by `writeup:` in data/projects.yml and stays at its notebook
 * URL, so nothing that links to it breaks. Its title, description, version and
 * date come from the page's own front matter. Research projects without a
 * write-up are listed after, so a project is never missing here just because it
 * has not been written up. Same `ocl-garden` shell as the notebook and writing
 * indexes.
 */

function WriteupEntry({
  project,
  papers,
}: {
  project: Project & { writeup: Writeup };
  papers: number;
}): ReactNode {
  const art = useBaseUrl(`/img/art/projects/${project.name}.svg`);
  const w = project.writeup;
  return (
    <article className="ocl-garden__card">
      <Link to={w.href} className="ocl-garden__link">
        <span className="ocl-garden__picture">
          <img src={art} alt="" loading="lazy" decoding="async" />
        </span>
        <span className="ocl-garden__body">
          <span className="ocl-garden__meta">
            <Stage status={project.tone} label={false} />
            <span>{project.name}</span>
          </span>
          <span className="ocl-garden__title">{w.title}</span>
          <span className="ocl-garden__summary">{w.description}</span>
          <span className="ocl-garden__meta">{writeupMeta(w)}</span>
        </span>
      </Link>
      <p className="ocl-garden__pages">
        {project.notebook !== w.href ? <Link to={project.notebook}>Experiments</Link> : null}
        <a href={project.repo} target="_blank" rel="noreferrer">
          Code ↗
        </a>
        {papers > 0 ? (
          <Link to={`/reading?project=${project.name}`}>
            {papers} {papers === 1 ? "paper" : "papers"} in Reading
          </Link>
        ) : null}
      </p>
    </article>
  );
}

/** A research project with no write-up yet: its drawing, objective and phase, to its notebook page. */
function Unwritten({ project }: { project: Project }): ReactNode {
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
          </span>
        </span>
      </Link>
    </article>
  );
}

export default function Research(): ReactNode {
  const { projects, papers } = usePluginData("ocl-lab-data") as LabData;
  const written = withWriteup(projects);
  const unwritten = projects.filter((p) => p.kind === "research" && !p.writeup);
  const fieldArt = useBaseUrl("/img/art/pages/mech-interp-2026.svg");

  return (
    <Layout
      title="Research"
      description="The overall write-up of each research project: what it set out to establish and what it found."
    >
      <main className="ocl-page ocl-research">
        <div className="ocl-index ocl-garden">
          <header className="ocl-garden__head">
            <p className="ocl-garden__count" aria-label={`${written.length} write-ups`}>
              {written.length}
            </p>
            <h1 className="ocl-garden__heading">Research</h1>
            <p className="ocl-garden__lede">
              The overall write-up of each project that has reached one. The
              experiments behind each are on the project's{" "}
              <Link to="/notebook">notebook</Link> page, and dated pieces are in{" "}
              <Link to="/writing">writing</Link>.
            </p>
          </header>

          <div className="ocl-garden__grid">
            {written.map((project) => (
              <WriteupEntry
                key={project.name}
                project={project}
                papers={papers.filter((p) => p.projects.includes(project.name)).length}
              />
            ))}
          </div>

          {unwritten.length > 0 ? (
            <section className="ocl-garden__desk" aria-label="No write-up yet">
              <h2 className="ocl-garden__deskTitle">No write-up yet</h2>
              <div className="ocl-garden__grid">
                {unwritten.map((project) => (
                  <Unwritten key={project.name} project={project} />
                ))}
              </div>
            </section>
          ) : null}

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
