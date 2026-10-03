import { useEffect, useState, type ReactNode } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { BuiltPage, LabData } from "@site/plugins/lab-data";

function Card({ page }: { page: BuiltPage }): ReactNode {
  const based = useBaseUrl(page.src);
  const href = page.external ? page.src : based;
  const imageBased = useBaseUrl(page.image ?? "");
  const image = page.image && (/^https?:/.test(page.image) ? page.image : imageBased);

  return (
    <figure className="ocl-card">
      <div
        className="ocl-card__preview"
        style={{ aspectRatio: `${page.ratio}` }}
      >
        {/* A heavy page (a 3D scene) gets a still, linked to the page, so the
            list doesn't run every scene at once. */}
        {image ? (
          <a href={href} target="_blank" rel="noreferrer" tabIndex={-1} aria-hidden="true">
            <img className="ocl-card__image" src={image} alt="" loading="lazy" decoding="async" />
          </a>
        ) : (
          <iframe
            className="ocl-card__frame"
            src={href}
            title={`${page.title} — live preview`}
            loading="lazy"
            tabIndex={-1}
            aria-hidden="true"
            sandbox="allow-scripts allow-same-origin"
          />
        )}
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

const slug = (topic: string) => "topic-" + topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

export default function Built(): ReactNode {
  const { built } = usePluginData("ocl-lab-data") as LabData;
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<string | null>(null);

  const q = query.trim().toLowerCase();
  const matches = (page: BuiltPage) => !q || `${page.title} ${page.what} ${page.topic}`.toLowerCase().includes(q);
  const topics = [...new Set(built.map((page) => page.topic))].map((topic) => ({
    topic,
    id: slug(topic),
    pages: built.filter((page) => page.topic === topic && matches(page)),
  }));
  const shown = topics.reduce((n, t) => n + t.pages.length, 0);

  // Highlight the topic being read: the last section whose heading has
  // scrolled past the top of the viewport.
  useEffect(() => {
    const onScroll = () => {
      let current: string | null = null;
      for (const t of topics) {
        const el = document.getElementById(t.id);
        if (el && el.getBoundingClientRect().top < 140) current = t.id;
      }
      setActive(current ?? topics.find((t) => t.pages.length)?.id ?? null);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [query]);

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

        <div className="ocl-built">
          <nav className="ocl-built__nav" aria-label="Topics on this page">
            <label className="ocl-built__search">
              <span className="ocl-built__searchLabel">Find a page</span>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="title or topic"
              />
            </label>
            <p className="ocl-built__count">
              {q ? `${shown} of ${built.length} pages` : `${built.length} pages · ${topics.length} topics`}
            </p>
            <ul className="ocl-built__topics">
              {topics.map((t) => (
                <li key={t.id}>
                  <a
                    href={`#${t.id}`}
                    className={`ocl-built__topic${active === t.id ? " is-active" : ""}${t.pages.length ? "" : " is-empty"}`}
                    aria-current={active === t.id ? "location" : undefined}
                  >
                    <span>{t.topic}</span>
                    <span className="ocl-built__n">{t.pages.length}</span>
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="ocl-built__main">
            {topics.filter((t) => t.pages.length).map((t) => (
              <section className="ocl-page__section ocl-built__section" key={t.id} id={t.id}>
                <h2 className="ocl-page__sectionTitle">
                  {t.topic} <span className="ocl-built__sectionCount">{t.pages.length}</span>
                </h2>
                <div className="ocl-cards">
                  {t.pages.map((page) => (
                    <Card key={page.name} page={page} />
                  ))}
                </div>
              </section>
            ))}
            {!shown && <p className="ocl-page__note">Nothing matches “{query}”.</p>}

            <p className="ocl-page__foot">
              Kept in <code>data/built.yml</code>. A local file is copied into the
              site on build; an entry with a <code>url</code> is embedded from
              wherever it is deployed.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
