import type { ReactNode } from "react";
import { useBlogPost } from "@docusaurus/plugin-content-blog/client";

/**
 * Tags and authors already appear in the front matter block, so the footer
 * only records when the file itself last changed.
 */
export default function BlogPostItemFooter(): ReactNode {
  const { metadata, isBlogPostPage } = useBlogPost();
  const { lastUpdatedAt } = metadata;

  if (!isBlogPostPage || !lastUpdatedAt) {
    return null;
  }

  return (
    <footer className="theme-doc-footer">
      <span className="theme-last-updated">
        Last edited <b>
          {new Intl.DateTimeFormat("en-GB", {
            day: "numeric",
            month: "long",
            year: "numeric",
            timeZone: "UTC",
          }).format(new Date(lastUpdatedAt))}
        </b>
      </span>
    </footer>
  );
}
