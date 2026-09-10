import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Paper } from "@site/plugins/lab-data";

/** First author's surname, from the "Surname, A., Other, B." form. */
function firstAuthor(authors: string): string {
  const first = authors.split(",")[0]?.trim() ?? authors;
  const multiple = authors.includes(",") && authors.split(",").length > 2;
  return multiple ? `${first} et al.` : first;
}

export function usePapers(): Paper[] {
  return (usePluginData("ocl-lab-data") as LabData).papers;
}

export function usePaper(id: string): Paper | undefined {
  return usePapers().find((paper) => paper.id === id);
}

/**
 * An inline citation, resolved from data/papers.yml by id. Renders
 * "(Cohen et al., 2024)", or "Cohen et al. (2024)" with `narrative`.
 *
 * A citation whose entry is not yet verified is marked, because a secondhand
 * reference that looks identical to a checked one is how a wrong venue
 * survives three drafts.
 */
export default function Cite({
  id,
  narrative = false,
  children,
}: {
  id: string;
  narrative?: boolean;
  children?: ReactNode;
}): ReactNode {
  const paper = usePaper(id);

  if (!paper) {
    return (
      <span className="ocl-cite ocl-cite--missing" title={`No entry "${id}" in data/papers.yml`}>
        [{id}?]
      </span>
    );
  }

  const name = children ?? firstAuthor(paper.authors);
  const label = narrative ? (
    <>
      {name} ({paper.year})
    </>
  ) : (
    <>
      ({name}, {paper.year})
    </>
  );

  const title = paper.verified
    ? `${paper.title}${paper.venue ? `. ${paper.venue} ${paper.year}` : ""}`
    : `${paper.title} — entry not verified; check the paper before citing`;

  const className = `ocl-cite${paper.verified ? "" : " ocl-cite--unverified"}`;

  return paper.url ? (
    <a className={className} href={paper.url} title={title} target="_blank" rel="noreferrer">
      {label}
    </a>
  ) : (
    <Link className={className} to={`/reading#${paper.id}`} title={title}>
      {label}
    </Link>
  );
}
