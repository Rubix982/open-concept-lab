import { useEffect, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import { usePluginData } from "@docusaurus/useGlobalData";
import useBaseUrl from "@docusaurus/useBaseUrl";
import type { BuiltPage, LabData, Paper, Project } from "@site/plugins/lab-data";
import { AGENTIC, type Agentic } from "@site/src/data/agentic";
import { ProjectCard } from "@site/src/components/Projects";

function shortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

/** A small drawing from static/img/art/steps/, beside a section's title. */
function Doodle({ name }: { name: string }): ReactNode {
  const src = useBaseUrl(`/img/art/steps/${name}.svg`);
  return <img className="ocl-home__doodle" src={src} alt="" aria-hidden="true" decoding="async" />;
}

function SectionHead({
  title,
  href,
  linkLabel,
  kicker,
  art,
}: {
  title: string;
  href: string;
  linkLabel: string;
  kicker?: string;
  /** A drawing in static/img/art/steps/ to sit beside the title. */
  art?: string;
}): ReactNode {
  return (
    <div className="ocl-home__sectionHead">
      <h2 className="ocl-home__sectionTitle">
        {art ? <Doodle name={art} /> : null}
        {title}
        {kicker ? <span className="ocl-home__kicker">{kicker}</span> : null}
      </h2>
      <Link className="ocl-home__sectionLink" to={href}>
        {linkLabel} →
      </Link>
    </div>
  );
}

function Bar({ done, total }: { done: number; total: number }): ReactNode {
  return (
    <span className="ocl-home__bar" aria-hidden="true">
      <span style={{ width: `${total ? Math.max((done / total) * 100, done ? 1.5 : 0) : 0}%` }} />
    </span>
  );
}

/** A piece's illustration, small, as the home page shows it. */
function Cover({ src, className }: { src?: string; className: string }): ReactNode {
  const url = useBaseUrl(src ?? "");
  if (!src) return null;
  return (
    <span className={className}>
      <img src={url} alt="" loading="lazy" decoding="async" />
    </span>
  );
}

function BuiltTile({ page }: { page: BuiltPage }): ReactNode {
  const local = useBaseUrl(page.src);
  const image = useBaseUrl(page.image ?? "");
  const href = page.external ? page.src : local;
  return (
    <a className="ocl-home__tile" href={href} target="_blank" rel="noreferrer">
      <span className="ocl-home__tileImage">
        {page.image ? (
          <img src={image} alt="" loading="lazy" decoding="async" />
        ) : (
          <span className="ocl-home__tileBlank">{page.title}</span>
        )}
      </span>
      <span className="ocl-home__tileTopic">{page.topic}</span>
      <span className="ocl-home__tileTitle">{page.title}</span>
    </a>
  );
}

// The sample is real terminal output, trimmed to its first lines for the card. The
// full run is on the tool's own page — a home-page card that invented plausible
// output would be exactly the fabrication /agentic says it refuses.
//
// `blurb` is a written one-liner rather than a truncation of `what`: the first
// sentence of the harness's description runs 287 characters against bearing's 53,
// which gives three cards of wildly different height for no reason a reader cares
// about.
function AgenticCard({
  href,
  title,
  blurb,
  sample,
  meta,
}: {
  href: string;
  title: string;
  blurb: string;
  sample: string;
  meta?: string;
}): ReactNode {
  return (
    <Link className="ocl-home__agent" to={href}>
      <pre className="ocl-home__agentSample">{sample.split("\n").slice(0, 7).join("\n")}</pre>
      <span className="ocl-home__agentTitle">{title}</span>
      <span className="ocl-home__agentWhat">{blurb}</span>
      {meta ? <span className="ocl-home__agentMeta">{meta}</span> : null}
    </Link>
  );
}

/** Tiny line icons for the jump links: one stroke each, drawn at 16px. */
const ICONS: Record<string, ReactNode> = {
  writing: <path d="M3 13 6 7l5-4 2 2-4 5-6 3Z M3 13l3.6-3.6" />,
  notebook: <path d="M2.5 3.5Q5 3 8 4v9q-3-1-5.5-.5Z M8 4q3-1 5.5-.5v9Q11 12 8 13" />,
  labs: <path d="M6 2h4M6.8 2v4L3 13h10L9.2 6V2M5 10h6" />,
  reading: <path d="M3 3h7l3 3v7H3Z M5.5 7h5M5.5 9.5h4" />,
  agentic: <path d="M8 2.5a5.5 5.5 0 0 1 5.5 5.5M8 13.5A5.5 5.5 0 0 1 2.5 8M12 6l1.5 2 1.5-2M4 10 2.5 8 1 10" />,
  shipped: <path d="M2 6l6-3 6 3-6 3Z M2 6v5l6 3 6-3V6M8 9v5" />,
  built: <path d="M2.5 13h11M3.5 13V9h3v4M6.5 13V5h3v8M9.5 13V7h3v6" />,
  about: <path d="M8 7.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM3 14c.5-3 2.4-4.5 5-4.5s4.5 1.5 5 4.5" />,
};

function Jump({ to, name, label }: { to: string; name: string; label: string }): ReactNode {
  return (
    <Link to={to} className={`ocl-chip ocl-chip--${name}`}>
      <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor"
        strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
        {ICONS[name]}
      </svg>
      {label}
    </Link>
  );
}

/**
 * A number that counts up to itself once the page is on screen. The server
 * renders the final value, so a reader without scripts, or who prefers less
 * motion, simply sees the number.
 */
function CountUp({ value }: { value: number }): ReactNode {
  const [shown, setShown] = useState(value);
  useEffect(() => {
    if (value === 0 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const start = performance.now();
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / 900);
      setShown(Math.round(value * (1 - Math.pow(1 - t, 3))));
      if (t < 1) frame = requestAnimationFrame(step);
    };
    setShown(0);
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <>{shown}</>;
}

/** A sticky note on the desk: what is moving now. */
function Note({
  to,
  tone,
  label,
  children,
}: {
  to: string;
  tone: string;
  label: string;
  children: ReactNode;
}): ReactNode {
  return (
    <Link to={to} className={`ocl-note ocl-note--${tone}`}>
      <span className="ocl-note__tape" aria-hidden="true" />
      <span className="ocl-note__label">{label}</span>
      <span className="ocl-note__text">{children}</span>
    </Link>
  );
}

function HeroArt(): ReactNode {
  const src = useBaseUrl("/img/art/home/hero.svg");
  return (
    <figure className="ocl-home__heroArt">
      <img
        src={src}
        alt="A small round creature standing for a language model, holding a magnifying glass up to its own thought: Paris crossed out, Rome written in."
        decoding="async"
      />
    </figure>
  );
}

function TrackThumb({ id }: { id: string }): ReactNode {
  const src = useBaseUrl(`/img/art/tracks/${id}.svg`);
  return <img className="ocl-home__trackArt" src={src} alt="" aria-hidden="true" loading="lazy" decoding="async" />;
}

export default function Home(): ReactNode {
  const { writing, papers, built, projects, labs } = usePluginData("ocl-lab-data") as LabData;

  const unchecked = papers.filter((p) => !p.verified);
  const read = papers.filter((p) => p.status === "read").length;
  const nextUp = papers
    .filter((p: Paper) => p.status === "to-read" && p.relevance === "high")
    .slice(0, 4);

  const [latest, ...earlier] = writing;
  const active = [...projects]
    .filter((p) => p.updated)
    .sort((a, b) => ((a.updated ?? "") < (b.updated ?? "") ? 1 : -1))[0];
  const recentBuilt = [...built]
    .map((page, i) => ({ page, i }))
    .sort((a, b) => (b.page.added ?? "").localeCompare(a.page.added ?? "") || a.i - b.i)
    .map(({ page }) => page)
    .slice(0, 8);
  const lastLab = labs.solved[0];

  return (
    <Layout
      title="Open Concept Lab"
      description="Experiments, writing, and interactive pages on knowledge editing and interpretability — what a model believes and how to tell whether a change took hold."
    >
      <div className="ocl-home">
        <header className="ocl-home__hero">
          <div className="ocl-home__masthead">
            <p className="ocl-home__eyebrow">
              <span className="ocl-home__wave" aria-hidden="true">✦</span> Hello, I'm Saif. This is my lab.
            </p>
            <h1 className="ocl-home__title">
              What a model{" "}
              <span className="ocl-home__squiggle">
                believes,
                <svg viewBox="0 0 200 16" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M2 10 C 22 2, 38 14, 58 8 S 96 2, 116 9 S 156 14, 176 7 S 194 6, 198 8" />
                </svg>
              </span>{" "}
              and how to tell when it changes.
            </h1>
            <p className="ocl-home__blurb">
              Experiments, writing, and interactive pages I built to understand
              something. Most of what is here is provisional and says so, and the
              reading list marks which citations I have actually checked.
            </p>
            <nav className="ocl-home__jump" aria-label="Sections">
              <Jump to="/writing" name="writing" label="Writing" />
              <Jump to="/notebook" name="notebook" label="Notebook" />
              <Jump to="/labs" name="labs" label="Labs" />
              <Jump to="/reading" name="reading" label="Reading" />
              <Jump to="/agentic" name="agentic" label="Agentic" />
              <Jump to="/shipped" name="shipped" label="Shipped" />
              <Jump to="/built" name="built" label="Built" />
              <Jump to="/about" name="about" label="About" />
            </nav>
            <p className="ocl-home__elsewhere">
              <a href="https://www.linkedin.com/in/suislam" target="_blank" rel="noreferrer">LinkedIn ↗</a>
              <a href="https://github.com/Rubix982" target="_blank" rel="noreferrer">GitHub ↗</a>
            </p>
          </div>
          <HeroArt />
        </header>

        <section className="ocl-home__desk" aria-label="What is moving now">
          <p className="ocl-home__deskLabel">On the desk right now</p>
          <div className="ocl-notes">
            {latest ? (
              <Note to={latest.permalink} tone="gold" label={`Latest writing · ${shortDate(latest.date)}`}>
                {latest.title}
              </Note>
            ) : null}
            {active ? (
              <Note to={active.notebook} tone="lilac" label={`Most recent plan · ${active.name}`}>
                {active.phase}
              </Note>
            ) : null}
            <Note to="/labs" tone="sage" label={`Labs · ${labs.done} of ${labs.total}`}>
              {lastLab ? `Last solved: ${lastLab.title}` : "Not started"}
              <Bar done={labs.done} total={labs.total} />
            </Note>
            {nextUp[0] ? (
              <Note to={`/reading#${nextUp[0].id}`} tone="pink" label="Reading next">
                {nextUp[0].title}
              </Note>
            ) : null}
          </div>
        </section>

        <dl className="ocl-home__stats">
          <div>
            <dt>Projects</dt>
            <dd><CountUp value={projects.length} /></dd>
          </div>
          <div>
            <dt>Pieces of writing</dt>
            <dd><CountUp value={writing.length} /></dd>
          </div>
          <div>
            <dt>Interactive pages</dt>
            <dd><CountUp value={built.length} /></dd>
          </div>
          <div>
            <dt>Papers read</dt>
            <dd>
              <CountUp value={read} />
              <span className="ocl-home__of"> / {papers.length}</span>
            </dd>
          </div>
          <div>
            <dt>Labs solved</dt>
            <dd>
              <CountUp value={labs.done} />
              <span className="ocl-home__of"> / {labs.total}</span>
            </dd>
          </div>
          <div>
            <dt>Citations unchecked</dt>
            <dd className={unchecked.length > 0 ? "ocl-tally--flag" : undefined}>{unchecked.length}</dd>
          </div>
        </dl>

        <section className="ocl-home__section">
          <SectionHead art="who-loop" title="Projects" kicker="each one's status is read from its own plan" href="/notebook" linkLabel="Notebook" />
          <div className="ocl-home__projects">
            {projects.map((project) => (
              <ProjectCard key={project.name} project={project} />
            ))}
          </div>
        </section>

        <section className="ocl-home__section">
          <SectionHead art="lab-retro" title="Writing" href="/writing" linkLabel="All writing" />
          {latest ? (
            <div className="ocl-home__writing">
              <article className="ocl-home__feature">
                <Link to={latest.permalink} tabIndex={-1} aria-hidden="true">
                  <Cover src={latest.cover} className="ocl-home__featureCover" />
                </Link>
                <time className="ocl-home__date" dateTime={latest.date}>
                  {shortDate(latest.date)}
                </time>
                <h3 className="ocl-home__featureTitle">
                  <Link to={latest.permalink}>{latest.title}</Link>
                </h3>
                {latest.summary ? <p className="ocl-home__featureSummary">{latest.summary}</p> : null}
                <Link className="ocl-home__more" to={latest.permalink}>
                  Read it →
                </Link>
              </article>
              {earlier.length > 0 ? (
                <ol className="ocl-home__earlier">
                  {earlier.slice(0, 4).map((entry) => (
                    <li key={entry.permalink} className={entry.cover ? "ocl-home__earlier--cover" : undefined}>
                      <Cover src={entry.cover} className="ocl-home__earlierCover" />
                      <time className="ocl-home__date" dateTime={entry.date}>
                        {shortDate(entry.date)}
                      </time>
                      <Link className="ocl-home__earlierTitle" to={entry.permalink}>
                        {entry.title}
                      </Link>
                      {entry.summary ? <p className="ocl-home__earlierSummary">{entry.summary}</p> : null}
                    </li>
                  ))}
                </ol>
              ) : null}
            </div>
          ) : (
            <p className="ocl-home__empty">
              Nothing published yet. Add a file to <code>blog/</code>.
            </p>
          )}
        </section>

        <section className="ocl-home__section">
          <SectionHead
            art="lab-break"
            title="Labs"
            kicker="deployment and security, one small broken system at a time"
            href="/labs"
            linkLabel="The full checklist"
          />
          <div className="ocl-home__labs">
            <ul className="ocl-home__tracks">
              {labs.tracks.map((t) => (
                <li key={t.id}>
                  <Link to={`/labs#track-${t.id}`} className="ocl-home__track">
                    <TrackThumb id={t.id} />
                    <span className="ocl-home__trackName">{t.title}</span>
                    <span className="ocl-home__trackCount">
                      {t.done} / {t.total}
                    </span>
                    <Bar done={t.done} total={t.total} />
                  </Link>
                </li>
              ))}
            </ul>
            <div className="ocl-home__solved">
              <p className="ocl-home__solvedLabel">Solved</p>
              {labs.solved.length > 0 ? (
                <ol>
                  {labs.solved.slice(0, 5).map((s) => (
                    <li key={s.title}>
                      {s.href ? (
                        <a href={s.href} target="_blank" rel="noreferrer">
                          {s.title}
                        </a>
                      ) : (
                        s.title
                      )}
                      <span>{s.section}</span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="ocl-home__empty">None yet.</p>
              )}
              <Link className="ocl-home__more" to="/notebook/opz/">
                What each one taught →
              </Link>
            </div>
          </div>
        </section>

        <section className="ocl-home__section">
          <SectionHead
            art="flow-run"
            title="Agentic"
            kicker="what keeps the work moving when nobody is at the desk"
            href="/agentic"
            linkLabel="All of it"
          />
          <div className="ocl-home__agents">
            {AGENTIC.map((item: Agentic) => (
              <AgenticCard
                key={item.name}
                href={`/agentic/${item.name}`}
                title={item.title}
                blurb={item.blurb}
                sample={item.sample}
                meta={item.where}
              />
            ))}
            <AgenticCard
              href="/agentic/practice"
              title="The practice, and its limits"
              blurb={
                "The boundary between what a loop may own and what a person must, and an " +
                "honest account of what none of it can catch."
              }
              sample={"A green harness is not a\nsound experiment.\n\nE-036 passed every gate\nand still measured two of\nsix criteria in ways that\ncould not answer their own\nquestions."}
            />
          </div>
        </section>

        <div className="ocl-home__split">
          <section className="ocl-home__section">
            <SectionHead art="flow-report" title="Reading next" href="/reading" linkLabel="Reading list" />
            {nextUp.length > 0 ? (
              <ol className="ocl-home__papers">
                {nextUp.map((paper) => (
                  <li key={paper.id}>
                    <Link to={`/reading#${paper.id}`}>{paper.title}</Link>
                    {paper.gives_me ? <p>{paper.gives_me}</p> : null}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="ocl-home__empty">Nothing marked next up.</p>
            )}
          </section>

          <section className="ocl-home__section">
            <SectionHead art="flow-queue" title="Built" kicker="recently added" href="/built" linkLabel={`All ${built.length} pages`} />
            <div className="ocl-home__tiles">
              {recentBuilt.map((page) => (
                <BuiltTile key={page.name} page={page} />
              ))}
            </div>
          </section>
        </div>

        <footer className="ocl-home__signoff">
          <Doodle name="who-person" />
          <p>
            Thanks for stopping by. If something here is wrong, I would rather
            know — <Link to="/about">here is how to tell me</Link>.
          </p>
        </footer>
      </div>
    </Layout>
  );
}
