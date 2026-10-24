import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { useBlogPost } from "@docusaurus/plugin-content-blog/client";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";
import {
  formatDate,
  isJournal,
  journalNumber,
} from "@site/src/components/writing/dates";
import { VoicesToggle } from "@site/src/components/writing/voices";

/** "10 September 2026" — day first, as a citation would set it. */
function formatLongDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

type OclFrontMatter = {
  /** One or two sentences under the title: what the piece argues. */
  standfirst?: string;
  /** draft | provisional | standing | superseded — shown in the record. */
  status?: string;
  /** Date of the last substantive revision, if it differs from the date. */
  revised?: string;
  /** Which project under ai/ this belongs to. */
  project?: string;
};

/**
 * The front matter block: title, standfirst, then labelled rows stating what
 * the piece is and how settled it is. Replaces the usual date-dot-readtime
 * line, because for writing that gets revised the revision state is the fact
 * a reader most needs.
 */
export default function BlogPostItemHeader(): ReactNode {
  const { metadata, frontMatter } = useBlogPost();
  const { title, date, readingTime, tags, authors } = metadata;
  const fm = frontMatter as OclFrontMatter;

  const { writing } = usePluginData("ocl-lab-data") as LabData;
  const entry = writing.find((e) => metadata.permalink.endsWith(e.permalink));
  const voices =
    entry && entry.notes > 0 ? (
      <VoicesToggle notes={entry.notes} author={authors[0]?.name?.split(" ")[0] ?? "Author"} />
    ) : null;

  if (isJournal(tags.map((t) => t.label.toLowerCase()))) {
    return (
      <>
        <JournalMasthead
          title={title}
          date={date}
          standfirst={fm.standfirst}
          number={entry ? journalNumber(writing, entry.slug) : undefined}
          minutes={typeof readingTime === "number" ? Math.ceil(readingTime) : undefined}
        />
        {voices}
      </>
    );
  }

  const author = authors[0];
  const authorName = author?.name;
  const authorUrl = author?.url;

  return (
    <header className="ocl-frontmatter">
      <h1 className="ocl-frontmatter__title">{title}</h1>

      {fm.standfirst ? (
        <p className="ocl-frontmatter__standfirst">{fm.standfirst}</p>
      ) : null}

      <dl className="ocl-frontmatter__record">
        <dt>Written</dt>
        <dd>
          <time dateTime={date}>{formatLongDate(date)}</time>
          {typeof readingTime === "number"
            ? `, ${Math.ceil(readingTime)} min read`
            : null}
        </dd>

        {fm.revised ? (
          <>
            <dt>Revised</dt>
            <dd className="ocl-revised">
              <time dateTime={fm.revised}>{formatLongDate(fm.revised)}</time>
            </dd>
          </>
        ) : null}

        {fm.status ? (
          <>
            <dt>Status</dt>
            <dd>
              <span className={`ocl-status ocl-status--${fm.status}`}>
                {fm.status}
              </span>
            </dd>
          </>
        ) : null}

        {fm.project ? (
          <>
            <dt>Project</dt>
            <dd>{fm.project}</dd>
          </>
        ) : null}

        {authorName ? (
          <>
            <dt>Written by</dt>
            <dd>
              {authorUrl ? (
                <Link to={authorUrl}>{authorName}</Link>
              ) : (
                authorName
              )}
            </dd>
          </>
        ) : null}

        {tags.length > 0 ? (
          <>
            <dt>Topics</dt>
            <dd>
              {tags.map((tag, i) => (
                <span key={tag.permalink}>
                  {i > 0 ? ", " : ""}
                  <Link to={tag.permalink}>{tag.label}</Link>
                </span>
              ))}
            </dd>
          </>
        ) : null}
      </dl>
      {voices}
    </header>
  );
}

/**
 * A journal entry is dated before it is titled: the day is the fact, the title
 * is whatever the thoughts turned out to be about. Set on a dot grid, the way a
 * notebook page is.
 */
function JournalMasthead({
  title,
  date,
  standfirst,
  number,
  minutes,
}: {
  title: string;
  date: string;
  standfirst?: string;
  number?: number;
  minutes?: number;
}): ReactNode {
  return (
    <header className="ocl-frontmatter ocl-journal">
      <div className="ocl-journal__date">
        <time dateTime={date}>
          <span className="ocl-journal__day">
            {formatDate(date, { day: "numeric" })}
          </span>
          <span className="ocl-journal__when">
            <span>{formatDate(date, { weekday: "long" })}</span>
            <span>{formatDate(date, { month: "long", year: "numeric" })}</span>
          </span>
        </time>
        <p className="ocl-journal__mark">
          <Link to="/writing/tags/journal">Journal</Link>
          {number ? <> · entry {String(number).padStart(2, "0")}</> : null}
          {minutes ? <> · {minutes} min</> : null}
        </p>
      </div>
      <h1 className="ocl-frontmatter__title ocl-journal__title">{title}</h1>
      {standfirst ? (
        <p className="ocl-frontmatter__standfirst">{standfirst}</p>
      ) : null}
    </header>
  );
}
