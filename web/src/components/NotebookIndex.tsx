import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { useDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import { useProjects } from "./Projects";
import Stage from "./writing/Stage";

/**
 * The projects, with the pages under each — the work the left rail used to do.
 *
 * The pages come from the resolved sidebar rather than from a list kept here,
 * so `sidebars.ts` stays the one place that knows what a project's pages are
 * and this cannot drift from the order they are in.
 *
 * Reads `useDocsSidebar()`, which throws outside a doc, so this belongs on the
 * notebook index and nowhere else. The home page keeps the plain cards.
 */
function pagesOf(items: PropSidebarItem[], name: string): PropSidebarItem[] {
  const entry = items.find((i) => "label" in i && i.label === name);
  return entry && entry.type === "category" ? entry.items : [];
}

function hrefOf(items: PropSidebarItem[], name: string): string | undefined {
  const entry = items.find((i) => "label" in i && i.label === name);
  if (!entry) return undefined;
  if (entry.type === "link") return entry.href;
  if (entry.type === "category") return entry.href;
  return undefined;
}

export default function NotebookIndex(): ReactNode {
  const projects = useProjects();
  const sidebar = useDocsSidebar();
  const items = sidebar?.items ?? [];

  return (
    <div className="ocl-nbindex">
      {projects.map((project) => {
        const pages = pagesOf(items, project.name);
        const href = hrefOf(items, project.name) ?? project.notebook;
        return (
          <section className="ocl-nbindex__row" key={project.name}>
            <h3 className="ocl-nbindex__name">
              <Link to={href}>{project.name}</Link>
            </h3>
            <p className="ocl-nbindex__phase" title={project.phaseDetail}>
              <Stage status={project.tone} label={false} />
              {project.phase}
            </p>
            <p className="ocl-nbindex__what">{project.what}</p>
            {pages.length ? (
              <p className="ocl-nbindex__pages">
                {pages.map((page) =>
                  page.type === "link" ? (
                    <Link key={page.href} to={page.href}>
                      {page.label}
                    </Link>
                  ) : null,
                )}
              </p>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
