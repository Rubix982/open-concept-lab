import type { ReactNode } from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import { useBlogPost } from "@docusaurus/plugin-content-blog/client";
import BlogPostItemContainer from "@theme/BlogPostItem/Container";
import BlogPostItemHeader from "@theme/BlogPostItem/Header";
import BlogPostItemContent from "@theme/BlogPostItem/Content";
import BlogPostItemFooter from "@theme/BlogPostItem/Footer";
import type { Props } from "@theme/BlogPostItem";

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
  const standfirst = (frontMatter as { standfirst?: string }).standfirst;
  const summary = standfirst ?? description;

  return (
    <article className="ocl-entry">
      <time className="ocl-entry__date" dateTime={date}>
        {formatShortDate(date)}
      </time>
      <div>
        <h2 className="ocl-entry__title">
          <Link to={permalink}>{title}</Link>
        </h2>
        {summary ? <p className="ocl-entry__summary">{summary}</p> : null}
        <div className="ocl-entry__meta">
          {typeof readingTime === "number" ? (
            <span>{Math.ceil(readingTime)} min read</span>
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
  const { isBlogPostPage } = useBlogPost();

  if (!isBlogPostPage) {
    return <BlogPostEntry />;
  }

  return (
    <BlogPostItemContainer className={clsx(className)}>
      <BlogPostItemHeader />
      <BlogPostItemContent>{children}</BlogPostItemContent>
      <BlogPostItemFooter />
    </BlogPostItemContainer>
  );
}
