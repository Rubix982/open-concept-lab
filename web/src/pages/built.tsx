import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { BuiltPage, LabData } from "@site/plugins/lab-data";

function Card({ page }: { page: BuiltPage }): ReactNode {
  const based = useBaseUrl(page.src);
  const href = page.external ? page.src : based;

  return (
    <figure className="ocl-card">
      <div
        className="ocl-card__preview"
        style={{ aspectRatio: `${page.ratio}` }}
      >
        <iframe
          className="ocl-card__frame"
          src={href}
          title={`${page.title} — live preview`}
          loading="lazy"
          tabIndex={-1}
          aria-hidden="true"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
      <figcaption className="ocl-card__body">
        <h3 className="ocl-card__title">
          <a href={href} target="_blank" rel="noreferrer">
            {page.title}
          </a>
        </h3>
        <p className="ocl-card__what">{page.what}</p>
        <p className="ocl-card__origin">
          {page.external ? `hosted at ${page.origin}` : `${page.origin}/`}
        </p>
      </figcaption>
    </figure>
  );
}

export default function Built(): ReactNode {
  const { built } = usePluginData("ocl-lab-data") as LabData;

  const topics = [...new Set(built.map((page) => page.topic))];

  return (
    <Layout
      title="Built"
      description="Interactive pages — explanations, explorers, and datasets you can poke at."
    >
      <div className="ocl-page">
        <header className="ocl-page__head">
          <h1 className="ocl-page__title">Built</h1>
          <p className="ocl-page__lede">
            Pages I made to understand something, each one live below. They are
            plain HTML, CSS and JavaScript, so they keep working without a
            build step. Open any of them full to actually use it — the previews
            are not interactive.
          </p>
        </header>

        {topics.map((topic) => (
          <section className="ocl-page__section" key={topic}>
            <h2 className="ocl-page__sectionTitle">{topic}</h2>
            <div className="ocl-cards">
              {built
                .filter((page) => page.topic === topic)
                .map((page) => (
                  <Card key={page.name} page={page} />
                ))}
            </div>
          </section>
        ))}

        <p className="ocl-page__foot">
          Kept in <code>data/built.yml</code>. A local file is copied into the
          site on build; an entry with a <code>url</code> is embedded from
          wherever it is deployed.
        </p>
      </div>
    </Layout>
  );
}
