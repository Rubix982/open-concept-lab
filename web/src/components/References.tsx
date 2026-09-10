import type { ReactNode } from "react";
import { usePapers } from "@site/src/components/Cite";

export type Reference = {
  authors: string;
  year: string | number;
  title: string;
  venue?: string;
  url?: string;
};

function Entry({ item }: { item: Reference }): ReactNode {
  // Author strings end in an initial's period; don't double it up.
  const authors = item.authors.replace(/\.\s*$/, "");
  return (
    <>
      {authors} ({item.year}).{" "}
      {item.url ? (
        <a href={item.url} target="_blank" rel="noreferrer">
          <cite>{item.title}</cite>
        </a>
      ) : (
        <cite>{item.title}</cite>
      )}
      {item.venue ? (
        <>
          . <span className="ocl-references__venue">{item.venue}</span>
        </>
      ) : null}
      .
    </>
  );
}

/**
 * A numbered reference list. Prefer `ids`, which pulls the metadata from
 * data/papers.yml so a paper is described in exactly one place; `items` is for
 * a one-off that does not belong in the reading list.
 */
export default function References({
  heading = "References",
  ids,
  items,
  children,
}: {
  heading?: string;
  ids?: string[];
  items?: Reference[];
  children?: ReactNode;
}): ReactNode {
  const papers = usePapers();

  const fromIds: Reference[] = (ids ?? []).flatMap((id) => {
    const paper = papers.find((p) => p.id === id);
    return paper
      ? [
          {
            authors: paper.authors,
            year: paper.year,
            title: paper.title,
            venue: paper.venue,
            url: paper.url,
          },
        ]
      : [];
  });

  const missing = (ids ?? []).filter(
    (id) => !papers.some((paper) => paper.id === id),
  );

  const all = [...fromIds, ...(items ?? [])];

  return (
    <section className="ocl-references">
      <h2 className="ocl-references__heading">{heading}</h2>
      <ol className="ocl-references__list">
        {all.length > 0
          ? all.map((item) => (
              <li key={`${item.title}-${item.year}`}>
                <Entry item={item} />
              </li>
            ))
          : children}
        {missing.map((id) => (
          <li key={id}>
            <span className="ocl-cite--missing">
              No entry &quot;{id}&quot; in data/papers.yml
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
