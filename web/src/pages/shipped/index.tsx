import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { SHIPPED, type Shipped } from "@site/src/data/shipped";

function Entry({ item }: { item: Shipped }): ReactNode {
  const page = `/shipped/${item.name}`;
  const image = useBaseUrl(item.image);
  return (
    <article className="ocl-ship__entry">
      <Link to={page} className="ocl-ship__entryShot" tabIndex={-1} aria-hidden="true">
        <img src={image} alt="" loading="lazy" decoding="async" />
      </Link>
      <div className="ocl-ship__entryBody">
        <h2 className="ocl-ship__entryTitle">
          <Link to={page}>{item.title}</Link>
        </h2>
        <p className="ocl-ship__entryWhat">{item.what}</p>
        <p className="ocl-ship__entryMeta">
          Live at <a href={item.url} target="_blank" rel="noreferrer">{new URL(item.url).host}</a> since {item.since}
        </p>
        <p className="ocl-ship__actions">
          <Link to={page} className="ocl-ship__primary">Read about it</Link>
          <a href={item.url} target="_blank" rel="noreferrer">Open {item.title} ↗</a>
        </p>
      </div>
    </article>
  );
}

export default function ShippedIndex(): ReactNode {
  return (
    <Layout title="Shipped" description="Tools that are deployed and in use, each with a page of its own.">
      <div className="ocl-page">
        <header className="ocl-page__head">
          <h1 className="ocl-page__title">Shipped</h1>
          <p className="ocl-page__lede">
            Tools that are deployed for anyone to use, each with a page of its
            own: who it is for, what it does, what it holds, and
            what it is still missing. The smaller pages, made in an afternoon to
            understand something, are on <Link to="/built">Built</Link>.
          </p>
        </header>
        {SHIPPED.map((item) => (
          <Entry key={item.name} item={item} />
        ))}
      </div>
    </Layout>
  );
}
