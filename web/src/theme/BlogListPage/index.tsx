import React, {useState, type ReactNode} from 'react';
import clsx from 'clsx';

import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {
  PageMetadata,
  HtmlClassNameProvider,
  ThemeClassNames,
} from '@docusaurus/theme-common';
import BlogLayout from '@theme/BlogLayout';
import BlogListPaginator from '@theme/BlogListPaginator';
import SearchMetadata from '@theme/SearchMetadata';
import type {Props} from '@theme/BlogListPage';
import BlogPostItem from '@theme/BlogPostItem';
import {BlogPostProvider} from '@docusaurus/plugin-content-blog/client';
import BlogListPageStructuredData from '@theme/BlogListPage/StructuredData';
import WritingDesk from '@site/src/components/writing/WritingDesk';
import {kindOf} from '@site/src/components/writing/dates';

type Item = Props['items'][number];
type Topic = {key: string; label: string; count: number};

/** Tags worth filtering by: any that more than one piece shares, or `journal`. */
function topicsOf(items: readonly Item[]): Topic[] {
  const counts = new Map<string, Topic>();
  for (const {content} of items) {
    for (const tag of content.metadata.tags) {
      const key = tag.permalink;
      const prior = counts.get(key);
      counts.set(key, {key, label: tag.label, count: (prior?.count ?? 0) + 1});
    }
  }
  return [...counts.values()]
    .filter((t) => t.count > 1 || t.label.toLowerCase() === 'journal')
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
    .slice(0, 5);
}

const STAGES = ['draft', 'provisional', 'standing', 'superseded'];

function statusOf(item: Item): string | undefined {
  return (item.content.frontMatter as {status?: string}).status;
}

function kindOfItem(item: Item): string {
  return kindOf(item.content.metadata.tags.map((t) => t.label.toLowerCase()));
}

function BlogListPageMetadata(props: Props): ReactNode {
  const {metadata} = props;
  const {
    siteConfig: {title: siteTitle},
  } = useDocusaurusContext();
  const {blogDescription, blogTitle, permalink} = metadata;
  const isBlogOnlyMode = permalink === '/';
  const title = isBlogOnlyMode ? siteTitle : blogTitle;
  return (
    <>
      <PageMetadata title={title} description={blogDescription} />
      <SearchMetadata tag="blog_posts_list" />
    </>
  );
}

function BlogListPageContent(props: Props): ReactNode {
  const {metadata, items, sidebar} = props;
  const {page} = metadata;
  const topics = topicsOf(items);
  const [topic, setTopic] = useState<string | null>(null);
  const [stage, setStage] = useState('');
  const [kind, setKind] = useState('');

  const stages = STAGES.filter((s) => items.some((i) => statusOf(i) === s));
  const kinds = [...new Set(items.map(kindOfItem))];

  const shown = items.filter(
    (item) =>
      (!topic || item.content.metadata.tags.some((t) => t.permalink === topic)) &&
      (!stage || statusOf(item) === stage) &&
      (!kind || kindOfItem(item) === kind),
  );

  return (
    <BlogLayout sidebar={sidebar}>
      <div className="ocl-index ocl-garden">
        <header className="ocl-garden__head">
          <p className="ocl-garden__count" aria-label={`${items.length} pieces`}>
            {items.length}
          </p>
          <h1 className="ocl-garden__heading">Writing</h1>
          <p className="ocl-garden__lede">
            Notes, essays, and journal entries, written while the research is
            still provisional. Pieces revised in place live in the{' '}
            <Link to="/notebook">notebook</Link>.
          </p>
        </header>

        <div className="ocl-garden__filters">
          <div className="ocl-garden__topics" role="group" aria-label="Topics">
            <span className="ocl-garden__topicsLabel">Topics</span>
            {topics.map((t) => (
              <button
                key={t.key}
                type="button"
                className="ocl-garden__topic"
                aria-pressed={topic === t.key}
                onClick={() => setTopic(topic === t.key ? null : t.key)}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="ocl-garden__selects">
            {stages.length > 0 ? (
              <label className="ocl-garden__select">
                <span className="sr-only">Growth stage</span>
                <select value={stage} onChange={(e) => setStage(e.target.value)}>
                  <option value="">All stages</option>
                  {stages.map((s) => (
                    <option key={s} value={s}>
                      {s[0].toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="ocl-garden__select">
              <span className="sr-only">Kind</span>
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                <option value="">All kinds</option>
                {kinds.map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {shown.length > 0 ? (
          <div className="ocl-garden__grid">
            {shown.map(({content: BlogPostContent}) => (
              <BlogPostProvider
                key={BlogPostContent.metadata.permalink}
                content={BlogPostContent}>
                <BlogPostItem>
                  <BlogPostContent />
                </BlogPostItem>
              </BlogPostProvider>
            ))}
          </div>
        ) : (
          <p className="ocl-garden__empty">Nothing growing here with those filters.</p>
        )}

        <BlogListPaginator metadata={metadata} />

        {page === 1 ? (
          <section className="ocl-garden__desk" aria-label="At the desk">
            <h2 className="ocl-garden__deskTitle">At the desk</h2>
            <WritingDesk />
          </section>
        ) : null}
      </div>
    </BlogLayout>
  );
}

export default function BlogListPage(props: Props): ReactNode {
  return (
    <HtmlClassNameProvider
      className={clsx(
        ThemeClassNames.wrapper.blogPages,
        ThemeClassNames.page.blogListPage,
      )}>
      <BlogListPageMetadata {...props} />
      <BlogListPageStructuredData {...props} />
      <BlogListPageContent {...props} />
    </HtmlClassNameProvider>
  );
}
