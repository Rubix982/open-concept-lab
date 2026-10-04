import { useEffect, useRef, useState, type ReactNode } from "react";
import Layout from "@theme/Layout";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { BuiltPage, LabData } from "@site/plugins/lab-data";

type View = "cards" | "compact" | "index";
const VIEWS: [View, string][] = [["cards", "Cards"], ["compact", "Compact"], ["index", "Index"]];
// cards a topic shows before "Show all", per view
const FOLD: Record<View, number> = { cards: 4, compact: 8, index: Infinity };

// Wrap the parts of `text` that match the search in <mark>.
function Hit({ text, q }: { text: string; q: string }): ReactNode {
  if (!q) return text;
  const at = text.toLowerCase().indexOf(q);
  if (at < 0) return text;
  return (
    <>
      {text.slice(0, at)}
      <mark className="ocl-built__hit">{text.slice(at, at + q.length)}</mark>
      <Hit text={text.slice(at + q.length)} q={q} />
    </>
  );
}

function useHref(page: BuiltPage) {
  const based = useBaseUrl(page.src);
  const imageBased = useBaseUrl(page.image ?? "");
  return {
    href: page.external ? page.src : based,
    image: page.image && (/^https?:/.test(page.image) ? page.image : imageBased),
  };
}

function Card({ page, q, compact }: { page: BuiltPage; q: string; compact?: boolean }): ReactNode {
  const { href, image } = useHref(page);
  return (
    <figure className={`ocl-card${compact ? " ocl-card--compact" : ""}`}>
      <div className="ocl-card__preview" style={{ aspectRatio: `${page.ratio}` }}>
        {/* A heavy page (a 3D scene) gets a still, linked to the page, so the
            list doesn't run every scene at once. Compact cards never run live. */}
        {image || compact ? (
          image ? (
            <a href={href} target="_blank" rel="noreferrer" tabIndex={-1} aria-hidden="true">
              <img className="ocl-card__image" src={image} alt="" loading="lazy" decoding="async" />
            </a>
          ) : (
            <a href={href} target="_blank" rel="noreferrer" tabIndex={-1} aria-hidden="true" className="ocl-card__placeholder">
              <span>{page.title}</span>
            </a>
          )
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
            <Hit text={page.title} q={q} />
          </a>
        </h3>
        {!compact && (
          <p className="ocl-card__what">
            <Hit text={page.what} q={q} />
          </p>
        )}
        <p className="ocl-card__origin">{page.external ? `hosted at ${page.origin}` : `${page.origin}/`}</p>
      </figcaption>
    </figure>
  );
}

function Row({ page, q }: { page: BuiltPage; q: string }): ReactNode {
  const { href } = useHref(page);
  return (
    <li className="ocl-built__row">
      <a href={href} target="_blank" rel="noreferrer" className="ocl-built__rowTitle">
        <Hit text={page.title} q={q} />
      </a>
      <span className="ocl-built__rowWhat">
        <Hit text={page.what} q={q} />
      </span>
      <span className="ocl-built__rowMeta">{page.added ?? ""}</span>
    </li>
  );
}

const slug = (topic: string) => "topic-" + topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const KEY = "ocl-built-view";

export default function Built(): ReactNode {
  const { built } = usePluginData("ocl-lab-data") as LabData;
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<string | null>(null);
  const [view, setView] = useState<View>("cards");
  const [open, setOpen] = useState<Set<string>>(new Set());
  const search = useRef<HTMLInputElement>(null);

  // the view is remembered per browser
  useEffect(() => {
    try {
      const v = localStorage.getItem(KEY) as View | null;
      if (v && FOLD[v] !== undefined) setView(v);
    } catch {}
  }, []);
  const pick = (v: View) => {
    setView(v);
    try { localStorage.setItem(KEY, v); } catch {}
  };

  // "/" jumps to the search box
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLElement && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
      if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey) { e.preventDefault(); search.current?.focus(); }
      if (e.key === "Escape" && e.target === search.current) { setQuery(""); search.current?.blur(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const q = query.trim().toLowerCase();
  const matches = (page: BuiltPage) => !q || `${page.title} ${page.what} ${page.topic}`.toLowerCase().includes(q);
  const topics = [...new Set(built.map((page) => page.topic))].map((topic) => ({
    topic,
    id: slug(topic),
    pages: built.filter((page) => page.topic === topic && matches(page)),
  }));
  const shown = topics.reduce((n, t) => n + t.pages.length, 0);
  // newest first; within a day, later in built.yml is newer
  const recent = built.map((p, i) => ({ p, i })).filter(({ p }) => p.added)
    .sort((a, b) => (b.p.added! > a.p.added! ? 1 : b.p.added! < a.p.added! ? -1 : b.i - a.i)).slice(0, 6).map(({ p }) => p);

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
  }, [query, view, open]);

  const toggle = (id: string) => setOpen((o) => { const n = new Set(o); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <Layout title="Built" description="Interactive pages — explanations, explorers, and datasets you can poke at.">
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
              <span className="ocl-built__searchLabel">
                Find a page <kbd className="ocl-built__kbd">/</kbd>
              </span>
              <input ref={search} type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="title, topic or words" />
            </label>
            <p className="ocl-built__count">
              {q ? `${shown} of ${built.length} pages` : `${built.length} pages · ${topics.length} topics`}
            </p>
            <div className="ocl-built__views" role="group" aria-label="View">
              {VIEWS.map(([v, label]) => (
                <button key={v} type="button" aria-pressed={view === v} onClick={() => pick(v)}>
                  {label}
                </button>
              ))}
            </div>
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
            {!q && view !== "index" && recent.length > 0 && (
              <section className="ocl-built__recent" aria-label="Recently added">
                <h2 className="ocl-page__sectionTitle">Recently added</h2>
                <div className="ocl-cards ocl-cards--compact">
                  {recent.map((page) => (
                    <Card key={page.name} page={page} q={q} compact />
                  ))}
                </div>
              </section>
            )}

            {topics.filter((t) => t.pages.length).map((t) => {
              const fold = q || open.has(t.id) ? Infinity : FOLD[view];
              const list = t.pages.slice(0, fold);
              const hidden = t.pages.length - list.length;
              return (
                <section className="ocl-page__section ocl-built__section" key={t.id} id={t.id}>
                  <h2 className="ocl-page__sectionTitle">
                    {t.topic} <span className="ocl-built__sectionCount">{t.pages.length}</span>
                  </h2>
                  {view === "index" ? (
                    <ul className="ocl-built__rows">
                      {list.map((page) => (
                        <Row key={page.name} page={page} q={q} />
                      ))}
                    </ul>
                  ) : (
                    <div className={`ocl-cards${view === "compact" ? " ocl-cards--compact" : ""}`}>
                      {list.map((page) => (
                        <Card key={page.name} page={page} q={q} compact={view === "compact"} />
                      ))}
                    </div>
                  )}
                  {(hidden > 0 || (open.has(t.id) && !q && t.pages.length > FOLD[view])) && (
                    <button type="button" className="ocl-built__more" onClick={() => toggle(t.id)} aria-expanded={open.has(t.id)}>
                      {open.has(t.id) ? "Show fewer" : `Show all ${t.pages.length}`}
                    </button>
                  )}
                </section>
              );
            })}
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
