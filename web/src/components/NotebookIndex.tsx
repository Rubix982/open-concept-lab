import { useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { useDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import type { Project } from "@site/plugins/lab-data";
import { useProjects } from "./Projects";
import Stage from "./writing/Stage";

/**
 * The notebook index, in the shape the writing index already has.
 *
 * Same shell, same classes: a count, a heading, a lede, a filter row, and a
 * card grid — `ocl-garden`, taken from `BlogListPage` rather than restated. The
 * two indexes answer the same question about different material, so a reader
 * who has learnt one should not have to learn the other.
 *
 * It also carries the pages under each project, which is the one thing the left
 * rail did that nothing else was doing after it was removed. Those links sit
 * outside the card's own link rather than inside it: a link inside a link is
 * invalid, and the browser resolves it by dropping one of them.
 *
 * The pages come from the resolved sidebar, so `sidebars.ts` stays the one place
 * that knows what a project's pages are and this cannot fall out of step with
 * their order. Reading the sidebar means `useDocsSidebar()`, which throws
 * outside a doc — so this belongs on the notebook index and nowhere else. The
 * home page keeps the plain cards.
 */
type Page = { label: string; href: string };

function pagesOf(items: PropSidebarItem[], name: string): Page[] {
  const entry = items.find((i) => "label" in i && i.label === name);
  if (!entry || entry.type !== "category") return [];
  return entry.items.flatMap((i) =>
    i.type === "link" ? [{ label: i.label, href: i.href }] : [],
  );
}

function hrefOf(items: PropSidebarItem[], name: string): string | undefined {
  const entry = items.find((i) => "label" in i && i.label === name);
  if (entry?.type === "link" || entry?.type === "category") return entry.href;
  return undefined;
}

function ProjectCard({
  project,
  href,
  pages,
}: {
  project: Project;
  href: string;
  pages: Page[];
}): ReactNode {
  const art = useBaseUrl(`/img/art/projects/${project.name}.svg`);
  return (
    <article className="ocl-garden__card">
      <Link to={href} className="ocl-garden__link">
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
      {pages.length ? (
        <p className="ocl-garden__pages">
          {pages.map((page) => (
            <Link key={page.href} to={page.href}>
              {page.label}
            </Link>
          ))}
        </p>
      ) : null}
    </article>
  );
}

/** A page that is not a project: the same card, its own drawing. */
function AroundCard({
  href,
  art,
  title,
  what,
}: {
  href: string;
  art: string;
  title: string;
  what: string;
}): ReactNode {
  const src = useBaseUrl(`/img/art/pages/${art}.svg`);
  return (
    <article className="ocl-garden__card">
      <Link to={href} className="ocl-garden__link">
        <span className="ocl-garden__picture">
          <img src={src} alt="" loading="lazy" decoding="async" />
        </span>
        <span className="ocl-garden__body">
          <span className="ocl-garden__title">{title}</span>
          <span className="ocl-garden__summary">{what}</span>
        </span>
      </Link>
    </article>
  );
}

const STAGES = ["draft", "provisional", "standing", "superseded"];

export default function NotebookIndex(): ReactNode {
  const projects = useProjects();
  const sidebar = useDocsSidebar();
  const items = sidebar?.items ?? [];
  const [stage, setStage] = useState<string | null>(null);

  const stages = STAGES.filter((s) => projects.some((p) => p.tone === s));
  const shown = stage ? projects.filter((p) => p.tone === stage) : projects;

  return (
    <div className="ocl-index ocl-garden">
      <header className="ocl-garden__head">
        <p className="ocl-garden__count" aria-label={`${projects.length} projects`}>
          {projects.length}
        </p>
        <h1 className="ocl-garden__heading">Notebook</h1>
        <p className="ocl-garden__lede">
          A living page per project, revised in place rather than dated — what it
          is trying to establish, what has been settled, and what is still open.
          Dated pieces live in <Link to="/writing">writing</Link>.
        </p>
      </header>

      <div className="ocl-garden__filters">
        <div className="ocl-garden__topics" role="group" aria-label="Stages">
          <span className="ocl-garden__topicsLabel">Stages</span>
          {stages.map((s) => (
            <button
              key={s}
              type="button"
              className="ocl-garden__topic"
              aria-pressed={stage === s}
              onClick={() => setStage(stage === s ? null : s)}
            >
              {s[0].toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {shown.length > 0 ? (
        <div className="ocl-garden__grid">
          {shown.map((project) => (
            <ProjectCard
              key={project.name}
              project={project}
              href={hrefOf(items, project.name) ?? project.notebook}
              pages={pagesOf(items, project.name)}
            />
          ))}
        </div>
      ) : (
        <p className="ocl-garden__empty">Nothing at that stage.</p>
      )}

      {/* Not projects, so they keep their own group — the same call the sidebar
          made — but the same card, with a drawing of their own. An earlier pass
          gave them the coverless form with a small icon instead, which made the
          one thing that should have been identical the one thing that was not:
          a reader reads the difference as a difference in kind, and these are
          pages like the rest. The drawings come from the same script, so they
          are in the same hand rather than near it. */}
      <section className="ocl-garden__desk" aria-label="Around the work">
        <h2 className="ocl-garden__deskTitle">Around the work</h2>
        <div className="ocl-garden__grid">
          <AroundCard
            href="/notebook/mech-interp-2026"
            art="mech-interp-2026"
            title="The field in 2026"
            what="Where work on model internals was judged this year, what each venue asked for, and which of those asks nothing here answers. Not a reading list."
          />
          <AroundCard
            href="/notebook/writing-here"
            art="writing-here"
            title="Writing here"
            what="The pieces this site gives a page — numbered figures, margin notes, claim blocks, references, mathematics — and the front matter each one expects. Doubles as the proof sheet."
          />
        </div>
      </section>
    </div>
  );
}
