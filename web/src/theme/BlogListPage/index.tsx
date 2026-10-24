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
import {formatDate} from '@site/src/components/writing/dates';

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

/** Consecutive items grouped under the month they were written. */
function byMonth(items: readonly Item[]): {month: string; items: Item[]}[] {
  const groups: {month: string; items: Item[]}[] = [];
  for (const item of items) {
    const month = formatDate(item.content.metadata.date, {
      month: 'long',
      year: 'numeric',
    });
    const last = groups[groups.length - 1];
    if (last?.month === month) last.items.push(item);
    else groups.push({month, items: [item]});
  }
  return groups;
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

  const shown = topic
    ? items.filter(({content}) =>
        content.metadata.tags.some((t) => t.permalink === topic),
      )
    : items;

  return (
    <BlogLayout sidebar={sidebar}>
      <div className="ocl-index">
        {page === 1 && (
          <>
            <p className="ocl-index__lede">
              Notes and essays written while the research is still provisional,
              newest first. Pieces that get revised instead of dated live in the{' '}
              <Link to="/notebook">notebook</Link>.
            </p>
            <WritingDesk />
          </>
        )}

        {topics.length > 0 ? (
          <div className="ocl-filter" role="group" aria-label="Show only">
            <button
              type="button"
              className="ocl-filter__chip"
              aria-pressed={topic === null}
              onClick={() => setTopic(null)}>
              All <span className="ocl-filter__count">{items.length}</span>
            </button>
            {topics.map((t) => (
              <button
                key={t.key}
                type="button"
                className="ocl-filter__chip"
                aria-pressed={topic === t.key}
                onClick={() => setTopic(topic === t.key ? null : t.key)}>
                {t.label} <span className="ocl-filter__count">{t.count}</span>
              </button>
            ))}
          </div>
        ) : null}

        <div className="ocl-timeline">
          {byMonth(shown).map((group) => (
            <section key={group.month} className="ocl-timeline__month">
              <h2 className="ocl-timeline__label">{group.month}</h2>
              {group.items.map(({content: BlogPostContent}) => (
                <BlogPostProvider
                  key={BlogPostContent.metadata.permalink}
                  content={BlogPostContent}>
                  <BlogPostItem>
                    <BlogPostContent />
                  </BlogPostItem>
                </BlogPostProvider>
              ))}
            </section>
          ))}
        </div>
        <BlogListPaginator metadata={metadata} />
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
