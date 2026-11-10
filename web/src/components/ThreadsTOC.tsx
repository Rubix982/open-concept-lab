import TOCItems from "@theme/TOCItems";
import type { ReactNode } from "react";
import { ThemeClassNames } from "@docusaurus/theme-common";
import { usePluginData } from "@docusaurus/useGlobalData";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import type { LabData } from "@site/plugins/lab-data";

/**
 * The contents of the threads view, for the rail.
 *
 * The threads content is an imported partial, so its headings never reach the
 * page's own table of contents -- Docusaurus builds that from the file it
 * compiles, and the partial is a different file. Without this the rail went on
 * listing the paper's sections while the body showed the backlog, which is a
 * contents list for something that is not on screen.
 *
 * The entries are generated into `data/record.yml` by the same pass that writes
 * the partial, read back off the page it just wrote, so the rail cannot name a
 * heading the page does not carry.
 */
export default function ThreadsTOC(): ReactNode {
  const { metadata } = useDoc();
  const data = usePluginData("ocl-lab-data") as LabData;
  const toc = data.record?.[metadata.id.split("/")[0]]?.toc;
  if (!toc?.length) return null;

  return (
    <div className={ThemeClassNames.docs.docTocDesktop}>
      <TOCItems
        toc={toc}
        minHeadingLevel={2}
        maxHeadingLevel={3}
        className="table-of-contents table-of-contents__left-border ocl-threadstoc"
        linkClassName="table-of-contents__link toc-highlight"
        linkActiveClassName="table-of-contents__link--active"
      />
    </div>
  );
}
