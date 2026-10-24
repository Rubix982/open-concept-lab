import { useState, type ReactNode } from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import { useBlogPost } from "@docusaurus/plugin-content-blog/client";
import BlogPostItemContainer from "@theme/BlogPostItem/Container";
import BlogPostItemHeader from "@theme/BlogPostItem/Header";
import BlogPostItemContent from "@theme/BlogPostItem/Content";
import BlogPostItemFooter from "@theme/BlogPostItem/Footer";
import type { Props } from "@theme/BlogPostItem";
import ReadingProgress from "@site/src/components/writing/ReadingProgress";
import { isJournal } from "@site/src/components/writing/dates";
import { VoicesContext } from "@site/src/components/writing/voices";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

/** Day-first, the way a date reads in a citation. */
function formatShortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

/**
 * In list view a post is one row of a record: date, title, what it argues.
 * In post view it is an article with a preprint-style front matter block.
 */
function BlogPostEntry(): ReactNode {
  const { metadata, frontMatter } = useBlogPost();
  const { permalink, title, date, description, tags, readingTime } = metadata;

  // The standfirst is written to be read in the index; the auto-excerpt is a
  // fallback for posts that don't have one.
  const { standfirst, status } = frontMatter as {
    standfirst?: string;
    status?: string;
  };
  const summary = standfirst ?? description;
  const journal = isJournal(tags.map((t) => t.label.toLowerCase()));
  const { writing } = usePluginData("ocl-lab-data") as LabData;
  const notes = writing.find((e) => permalink.endsWith(e.permalink))?.notes ?? 0;

  return (
    <article
      className={clsx("ocl-entry", {
        "ocl-entry--journal": journal,
        [`ocl-entry--${status}`]: Boolean(status),
      })}
    >
      <time className="ocl-entry__date" dateTime={date}>
        {formatShortDate(date)}
      </time>
      <span className="ocl-entry__node" aria-hidden="true" />
      <div>
        {journal ? <p className="ocl-entry__kicker">Journal</p> : null}
        <h2 className="ocl-entry__title">
          <Link to={permalink}>{title}</Link>
        </h2>
        {summary ? <p className="ocl-entry__summary">{summary}</p> : null}
        <div className="ocl-entry__meta">
          {typeof readingTime === "number" ? (
            <span>{Math.ceil(readingTime)} min read</span>
          ) : null}
          {notes > 0 ? (
            <span className="ocl-entry__with">
              with Claude · {notes} {notes === 1 ? "note" : "notes"}
            </span>
          ) : null}
          {tags.length > 0 ? (
            <span>
              {tags.map((tag, i) => (
                <span key={tag.permalink}>
                  {i > 0 ? ", " : ""}
                  <Link to={tag.permalink}>{tag.label}</Link>
                </span>
              ))}
            </span>
          ) : null}
        </div>
      </div>
    </article>
  );
}

export default function BlogPostItem({ children, className }: Props): ReactNode {
  const { isBlogPostPage, metadata } = useBlogPost();
  const [mineOnly, setMineOnly] = useState(false);

  if (!isBlogPostPage) {
    return <BlogPostEntry />;
  }

  const journal = isJournal(metadata.tags.map((t) => t.label.toLowerCase()));

  return (
    <VoicesContext.Provider value={{ mineOnly, setMineOnly }}>
    <BlogPostItemContainer
      className={clsx(className, "ocl-post", {
        "ocl-post--journal": journal,
        "ocl-post--mine-only": mineOnly,
      })}
    >
      <ReadingProgress />
      <BlogPostItemHeader />
      <BlogPostItemContent>{children}</BlogPostItemContent>
      <BlogPostItemFooter />
    </BlogPostItemContainer>
    </VoicesContext.Provider>
  );
}
