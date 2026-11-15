import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import clsx from "clsx";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";

/**
 * The pages of the project this page belongs to, at the head of the rail.
 *
 * Removing the left rail was the right call for moving between projects — the
 * index does that, and better. What it also removed, and what I did not account
 * for, was moving *within* one: from a project's overview to its paper there
 * was nothing left but a link in the third paragraph and a row in a table two
 * screens down. A reader who wanted the paper had to read the overview first to
 * find out where it was.
 *
 * So the one thing the sidebar did that nothing replaced comes back, in the
 * place it used to be. Projects with a single page get nothing, because a list
 * of one is not navigation.
 */
function entryFor(items: PropSidebarItem[], project: string) {
  return items.find(
    (i) => "label" in i && i.label === project && i.type === "category",
  );
}

export default function ProjectPages(): ReactNode {
  const { metadata } = useDoc();
  const sidebar = useDocsSidebar();
  const project = metadata.id.split("/")[0];
  const entry = entryFor(sidebar?.items ?? [], project);
  if (!entry || entry.type !== "category") return null;

  const pages = [
    ...(entry.href ? [{ label: "Overview", href: entry.href }] : []),
    ...entry.items.flatMap((i) =>
      i.type === "link" ? [{ label: i.label, href: i.href }] : [],
    ),
  ];
  if (pages.length < 2) return null;

  const here = metadata.permalink.replace(/\/$/, "");

  return (
    <nav className="ocl-pages" aria-label={`Pages in ${project}`}>
      <div className="ocl-pages__head">{project}</div>
      <ul className="ocl-pages__list">
        {pages.map((page) => {
          const current = page.href.replace(/\/$/, "") === here;
          return (
            <li key={page.href}>
              <Link
                to={page.href}
                className={clsx("ocl-pages__link", { "is-here": current })}
                aria-current={current ? "page" : undefined}
              >
                {page.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
