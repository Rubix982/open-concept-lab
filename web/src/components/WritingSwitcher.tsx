import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { useLocation } from "@docusaurus/router";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

function shortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(new Date(iso));
}

/**
 * Moving between pieces without leaving the one you're reading. Sits above the
 * contents in the same rail, so it costs no horizontal space and stays in view
 * while you scroll.
 */
export default function WritingSwitcher(): ReactNode {
  const { writing } = usePluginData("ocl-lab-data") as LabData;
  const { pathname } = useLocation();

  if (writing.length < 2) {
    return null;
  }

  const here = pathname.replace(/\/$/, "");

  return (
    <nav className="ocl-switcher" aria-label="Other writing">
      <p className="ocl-switcher__title">Writing</p>
      <ul className="ocl-switcher__list">
        {writing.map((entry) => {
          const current = here.endsWith(`/${entry.slug}`);
          return (
            <li key={entry.permalink}>
              <Link
                className={`ocl-switcher__link${current ? " ocl-switcher__link--current" : ""}`}
                to={entry.permalink}
                aria-current={current ? "page" : undefined}
              >
                <span className="ocl-switcher__date">{shortDate(entry.date)}</span>
                {entry.title}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
