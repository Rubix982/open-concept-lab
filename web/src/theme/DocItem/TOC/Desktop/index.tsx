import TOC from "@theme/TOC";
import { ThemeClassNames } from "@docusaurus/theme-common";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";
import RecordPanel from "@site/src/components/RecordPanel";
import { usePaperView } from "@site/src/components/paperView";
import type { ReactNode } from "react";

/**
 * The contents rail on a doc page: the state of the record, then the contents
 * of whichever view is showing.
 *
 * This replaces the original rather than wrapping it, because the original
 * passes the whole `toc` straight through and the whole `toc` is the problem.
 * Docusaurus resolves an imported partial's headings into the importing page's
 * table of contents, so the paper's list already carries the threads view's
 * headings -- the rail was listing the backlog underneath the paper's sections
 * while the paper was on screen, and listing the paper's sections while the
 * backlog was. One list, two views, so it is split here by the ids the
 * generator recorded in `data/record.yml`.
 *
 * Splitting the page's own list, rather than rendering a second one from the
 * generated data, keeps each heading's text, level and anchor coming from the
 * compiled page. The generated side carries ids and nothing else, so there is
 * no second copy of the words that could go stale.
 *
 * Wrapping `@theme/TOC` instead of this component looked equivalent and was
 * not: the blog renders a TOC too, and `RecordPanel` reads `useDoc()`, so three
 * writing pages failed static generation with a context error. This component
 * only ever mounts inside a doc.
 */
export default function DocItemTOCDesktop(): ReactNode {
  const { toc, frontMatter, metadata } = useDoc();
  const { view } = usePaperView();
  const data = usePluginData("ocl-lab-data") as LabData;

  const threadIds = new Set(data.record?.[metadata.id.split("/")[0]]?.toc ?? []);
  const shown = threadIds.size
    ? toc.filter((item) => threadIds.has(item.id) === (view === "threads"))
    : toc;

  return (
    <>
      <RecordPanel />
      <div className="ocl-rail" data-view={view} key={view}>
        <TOC
          toc={shown}
          minHeadingLevel={frontMatter.toc_min_heading_level}
          maxHeadingLevel={frontMatter.toc_max_heading_level}
          className={ThemeClassNames.docs.docTocDesktop}
        />
      </div>
    </>
  );
}
