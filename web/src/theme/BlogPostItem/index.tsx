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
import Stage from "@site/src/components/writing/Stage";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

import useBaseUrl from "@docusaurus/useBaseUrl";
import { ageOf, kindOf } from "@site/src/components/writing/dates";

/** A small drawing for an entry with no stage set, by what kind of piece it is. */
function KindIcon({ kind }: { kind: string }): ReactNode {
  return (
    <svg
      className="ocl-stage__icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {kind === "Journal" ? (
        // a pen nib
        <>
          <path d="M3 13 6 7l5-4 2 2-4 5-6 3Z" />
          <path d="M3 13l3.6-3.6" />
        </>
      ) : (
        // a folded page
        <>
          <path d="M4 2h5.5L12 4.5V14H4Z" />
          <path d="M9.5 2v2.5H12M6 8h4M6 10.5h4" />
        </>
      )}
    </svg>
  );
}

/**
 * In list view a post is a card in the garden: a large one, picture first, when
 * the piece has an illustration; a compact one, led by its stage of growth,
 * when it doesn't. In post view it is an article with a front matter block.
 */
function BlogPostEntry(): ReactNode {
  const { metadata, frontMatter } = useBlogPost();
  const { permalink, title, date, description, tags } = metadata;

  // The standfirst is written to be read in the index; the auto-excerpt is a
  // fallback for posts that don't have one.
  const { standfirst, status } = frontMatter as {
    standfirst?: string;
    status?: string;
  };
  const summary = standfirst ?? description;
  const labels = tags.map((t) => t.label.toLowerCase());
  const kind = kindOf(labels);
  const { writing, builtAt } = usePluginData("ocl-lab-data") as LabData;
  const entry = writing.find((e) => permalink.endsWith(e.permalink));
  const notes = entry?.notes ?? 0;
  const cover = useBaseUrl(entry?.cover ?? "");

  const meta = (
    <p className="ocl-garden__meta">
      <span>{kind}</span>
      {status ? <Stage status={status} label={false} /> : <span aria-hidden="true">·</span>}
      <time dateTime={date} title={date.slice(0, 10)}>
        {ageOf(date, builtAt)}
      </time>
      {notes > 0 ? (
        <span className="ocl-entry__with">
          · with Claude
        </span>
      ) : null}
    </p>
  );

  if (entry?.cover) {
    return (
      <article className={clsx("ocl-garden__card", { "ocl-garden__card--journal": isJournal(labels) })}>
        <Link to={permalink} className="ocl-garden__link">
          <span className="ocl-garden__picture">
            <img src={cover} alt="" loading="lazy" />
          </span>
          <span className="ocl-garden__body">
            <span className="ocl-garden__title">{title}</span>
            {summary ? <span className="ocl-garden__summary">{summary}</span> : null}
            {meta}
          </span>
        </Link>
      </article>
    );
  }

  return (
    <article className="ocl-garden__item">
      <Link to={permalink} className="ocl-garden__link">
        <span className={`ocl-garden__icon ocl-stage ocl-stage--${status ?? "none"}`}>
          {status ? <Stage status={status} label={false} /> : <KindIcon kind={kind} />}
        </span>
        <span className="ocl-garden__body">
          <span className="ocl-garden__title">{title}</span>
          {summary ? <span className="ocl-garden__summary">{summary}</span> : null}
          {meta}
        </span>
      </Link>
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
