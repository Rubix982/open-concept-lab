import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import type { SomedayItem, SomedayReference } from "@site/plugins/lab-data";

const KIND: Record<string, { label: string; tone: number }> = {
  business: { label: "Business", tone: 4 },
  try: { label: "Try", tone: 3 },
  learn: { label: "Learn", tone: 2 },
  make: { label: "Make", tone: 1 },
};

const STATUS: Record<string, string> = {
  spark: "A spark",
  exploring: "Exploring",
  tried: "Tried",
  project: "Became a project",
  "let-go": "Let go",
};

/** "25 Oct 2026", in UTC so the build and the browser agree. */
function day(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(`${iso}T00:00:00Z`),
  );
}

/** "arxiv.org", so a reader sees where a link goes before following it. */
function host(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** Groups in the order they first appear; ungrouped references sit under one plain heading. */
function grouped(refs: SomedayReference[]): [string, SomedayReference[]][] {
  const groups = new Map<string, SomedayReference[]>();
  for (const ref of refs) {
    const name = ref.group ?? "Sources";
    groups.set(name, [...(groups.get(name) ?? []), ref]);
  }
  return [...groups.entries()];
}

function References({ refs }: { refs: SomedayReference[] }): ReactNode {
  return (
    <section className="ocl-idea__refs" aria-labelledby="ocl-idea-refs">
      <h2 id="ocl-idea-refs" className="ocl-idea__refs-title">References</h2>
      {grouped(refs).map(([name, items]) => (
        <div key={name} className="ocl-idea__refs-group">
          <h3 className="ocl-idea__refs-group-title">{name}</h3>
          <ul className="ocl-idea__refs-list">
            {items.map((ref) => (
              <li key={ref.url} className="ocl-idea__ref">
                <span className="ocl-idea__ref-host">{host(ref.url)}</span>
                <a href={ref.url} target="_blank" rel="noreferrer" className="ocl-idea__ref-link">
                  {/* the arrow stays on the title's last line instead of wrapping alone */}
                  {ref.title}{" "}↗
                </a>
                {ref.note ? <p className="ocl-idea__ref-note">{ref.note}</p> : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

/**
 * One idea from someday/, given room: the note's line as a title, the why as a
 * standfirst, and the longer thinking below it at reading width.
 */
export default function SomedayIdea({ idea }: { idea: SomedayItem }): ReactNode {
  const kind = KIND[idea.kind] ?? { label: idea.kind, tone: 1 };
  const external = idea.link && /^https?:/.test(idea.link);
  return (
    <Layout title={idea.what} description={idea.why ?? `${kind.label} · something I want to do someday`}>
      <article className="ocl-page ocl-idea">
        <Link to="/someday" className="ocl-idea__back">← Someday</Link>
        <p className={`ocl-idea__meta ocl-window--tone${kind.tone}`}>
          <span className="ocl-idea__kind">{kind.label}</span>
          {STATUS[idea.status] ?? idea.status} · written down {day(idea.added)}
          {idea.words ? ` · ${idea.words} words` : ""}
        </p>
        <h1 className="ocl-idea__title">{idea.what}</h1>
        {idea.why ? <p className="ocl-idea__why">{idea.why}</p> : null}
        {idea.note ? <p className="ocl-idea__letgo">Let go: {idea.note}</p> : null}
        {idea.body ? (
          // our own Markdown, escaped and rendered at build time by the plugin
          <div className="ocl-idea__body" dangerouslySetInnerHTML={{ __html: idea.body }} />
        ) : (
          <p className="ocl-page__note">Nothing more written yet. The line above is the whole of it, for now.</p>
        )}
        {idea.references?.length ? <References refs={idea.references} /> : null}
        {idea.link ? (
          external ? (
            <a className="ocl-profile__btn ocl-profile__btn--primary" href={idea.link} target="_blank" rel="noreferrer">Where it went ↗</a>
          ) : (
            <Link className="ocl-profile__btn ocl-profile__btn--primary" to={idea.link}>Where it went →</Link>
          )
        ) : null}
      </article>
    </Layout>
  );
}
