import { useEffect, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import { usePluginData } from "@docusaurus/useGlobalData";
import useBaseUrl from "@docusaurus/useBaseUrl";
import type { BuiltPage, LabData, Paper, Project } from "@site/plugins/lab-data";
import { AGENTIC, GUIDES, type Agentic, type Guide } from "@site/src/data/agentic";
import { ProjectCard } from "@site/src/components/Projects";
import Profile from "@site/src/components/Profile";

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

/** Progress: solved in full colour, built-but-unsolved lighter, the rest empty. */
function Bar({ done, built = done, total }: { done: number; built?: number; total: number }): ReactNode {
  const pct = (n: number) => `${total ? Math.max((n / total) * 100, n ? 1.5 : 0) : 0}%`;
  return (
    <span className="ocl-home__bar" aria-hidden="true">
      <span style={{ width: pct(done) }} />
      <span className="ocl-home__barBuilt" style={{ width: pct(built - done) }} />
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

const topicSlug = (topic: string) =>
  "topic-" + topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

/** One built page in a little browser window: three dots, an address bar, the still. */
function BuiltWindow({
  page,
  tone,
  featured = false,
}: {
  page: BuiltPage;
  tone: number;
  featured?: boolean;
}): ReactNode {
  const local = useBaseUrl(page.src);
  const image = useBaseUrl(page.image ?? "");
  const href = page.external ? page.src : local;
  const address = page.external ? page.src.replace(/^https?:\/\//, "") : `demos/${page.name}`;
  return (
    <a
      className={`ocl-window ocl-window--tone${tone}${featured ? " ocl-window--featured" : ""}`}
      href={href}
      target="_blank"
      rel="noreferrer"
    >
      <span className="ocl-window__chrome" aria-hidden="true">
        <span className="ocl-window__dots"><i /><i /><i /></span>
        <span className="ocl-window__address">{address}</span>
      </span>
      <span className="ocl-window__screen">
        {page.image ? (
          <img src={image} alt="" loading="lazy" decoding="async" />
        ) : (
          <span className="ocl-window__blank">
            <span>{page.title}</span>
          </span>
        )}
      </span>
      <span className="ocl-window__caption">
        <span className="ocl-window__topic">{page.topic}</span>
        <span className="ocl-window__title">{page.title}</span>
        <span className="ocl-window__what">{page.what}</span>
        {featured ? <span className="ocl-window__open">Open it ↗</span> : null}
      </span>
    </a>
  );
}

/** A band of its own: a kicker, a headline that carries a number, one plain sentence, a way in. */
function Band({
  id,
  tone,
  kicker,
  title,
  lede,
  href,
  cta,
  children,
}: {
  id: string;
  tone: string;
  kicker: string;
  title: ReactNode;
  lede: ReactNode;
  href: string;
  cta: string;
  children: ReactNode;
}): ReactNode {
  return (
    <section className={`ocl-showcase ocl-band ocl-band--${tone}`} aria-labelledby={id}>
      <div className="ocl-showcase__head">
        <div>
          <p className="ocl-showcase__kicker">{kicker}</p>
          <h2 id={id} className="ocl-showcase__title">{title}</h2>
          <p className="ocl-showcase__lede">{lede}</p>
        </div>
        <Link className="ocl-profile__btn ocl-profile__btn--primary" to={href}>
          {cta}
        </Link>
      </div>
      {children}
    </section>
  );
}

type Step = { art: string; title: string; text: string };

/** How the thing works, as a row of drawings joined by arrows. */
function Steps({ steps, label }: { steps: Step[]; label: string }): ReactNode {
  return (
    <ol className="ocl-steps" aria-label={label}>
      {steps.map((step, i) => (
        <li key={step.art} className="ocl-steps__step" style={{ animationDelay: `${i * 70}ms` }}>
          <Doodle name={step.art} />
          <span className="ocl-steps__n">{String(i + 1).padStart(2, "0")}</span>
          <span className="ocl-steps__title">{step.title}</span>
          <span className="ocl-steps__text">{step.text}</span>
        </li>
      ))}
    </ol>
  );
}

// Captions are the ones /labs and /agentic already use, shortened, so the home
// page cannot describe the loop differently from the page it links to.
const LAB_LOOP: Step[] = [
  { art: "lab-break", title: "Break it", text: "A real incident, shrunk to run on a laptop." },
  { art: "lab-diagnose", title: "Diagnose it", text: "Find the cause from the symptoms, not the answer." },
  { art: "lab-fix", title: "Fix it", text: "The smallest change that removes the cause." },
  { art: "lab-prove", title: "Prove it", text: "A check that fails on a cover-up, not only on the bug." },
  { art: "lab-retro", title: "Write it down", text: "Five lines: what broke, why, what it taught." },
];

const AGENT_FLOW: Step[] = [
  { art: "flow-queue", title: "Queue", text: "Only pre-registered work, expected verdict written first." },
  { art: "flow-preflight", title: "Preflight", text: "Gates that refuse before anything touches the network." },
  { art: "flow-run", title: "Run", text: "Each job under a budget it may not outlive." },
  { art: "flow-triage", title: "Triage", text: "Failures sorted by cause; only the unknown one needs me." },
  { art: "flow-report", title: "Report", text: "Readable mid-run, including what it did not check." },
];

/** "Meng, Bau, Andonian" -> "Meng et al." */
function firstAuthor(authors: string): string {
  const parts = authors.split(/,| and /).map((a) => a.trim()).filter(Boolean);
  return parts.length > 1 ? `${parts[0]} et al.` : parts[0] ?? "";
}

/** The built pages get a whole band: one featured, a row of windows, and every topic. */
function BuiltShowcase({ built, recent }: { built: BuiltPage[]; recent: BuiltPage[] }): ReactNode {
  const topics = [...new Set(built.map((page) => page.topic))].map((topic) => ({
    topic,
    count: built.filter((page) => page.topic === topic).length,
  }));
  const toneOf = (topic: string) => (topics.findIndex((t) => t.topic === topic) % 6) + 1;
  const featured = recent.find((page) => page.image) ?? recent[0];
  // newest first, but no more than two from one topic, so a run of brick
  // models does not crowd out everything else
  const perTopic = new Map<string, number>();
  const rest = recent
    .filter((page) => page !== featured)
    .filter((page) => {
      const n = perTopic.get(page.topic) ?? 0;
      perTopic.set(page.topic, n + 1);
      return n < 2;
    })
    .slice(0, 6);
  if (!featured) return null;
  return (
    <Band
      id="built-heading"
      tone="dots"
      kicker="Built to understand something"
      title={<><CountUp value={built.length} /> interactive pages, {topics.length} topics</>}
      lede="When reading about a thing was not enough, I made a page I could poke at. Every one of these opens and runs."
      href="/built"
      cta={`Browse all ${built.length} →`}
    >
      <div className="ocl-showcase__grid">
        <BuiltWindow page={featured} tone={toneOf(featured.topic)} featured />
        <div className="ocl-showcase__rest">
          {rest.map((page) => (
            <BuiltWindow key={page.name} page={page} tone={toneOf(page.topic)} />
          ))}
        </div>
      </div>

      <nav className="ocl-showcase__topics" aria-label="Built pages by topic">
        {topics.map((t) => (
          <Link
            key={t.topic}
            to={`/built#${topicSlug(t.topic)}`}
            className={`ocl-showcase__topic ocl-window--tone${toneOf(t.topic)}`}
          >
            {t.topic} <span>{t.count}</span>
          </Link>
        ))}
      </nav>
    </Band>
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
  name,
  href,
  external = false,
  title,
  blurb,
  sample,
  meta,
}: {
  name: string;
  href: string;
  external?: boolean;
  title: string;
  blurb: string;
  sample: string;
  meta?: string;
}): ReactNode {
  const art = useBaseUrl(`/img/art/tools/${name}.svg`);
  return (
    <Link
      className="ocl-home__agent ocl-term"
      to={href}
      {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
    >
      <span className="ocl-term__window">
        <span className="ocl-term__bar" aria-hidden="true">
          <span className="ocl-window__dots"><i /><i /><i /></span>
          <span className="ocl-term__name">{meta ?? name}</span>
        </span>
        <pre className="ocl-term__screen">{sample.split("\n").slice(0, 7).join("\n")}</pre>
      </span>
      <span className="ocl-term__body">
        <img className="ocl-term__art" src={art} alt="" aria-hidden="true" loading="lazy" decoding="async" />
        <span>
          <span className="ocl-home__agentTitle">{title}</span>
          <span className="ocl-home__agentWhat">{blurb}</span>
          <span className="ocl-term__open">{external ? "Read it on GitHub ↗" : "Read how it works →"}</span>
        </span>
      </span>
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
  someday: <path d="M6 13h4M6.5 11h3M8 2.5a4 4 0 0 0-2.4 7.2c.5.4.9 1 .9 1.3h3c0-.3.4-.9.9-1.3A4 4 0 0 0 8 2.5Z" />,
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
        alt="A small round creature holding a magnifying glass up to its own thought: a bug crossed out, a tick, and a pair of code brackets."
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
    .slice(0, 24);
  const lastLab = labs.solved[0];

  return (
    <Layout
      title="Open Concept Lab"
      description="Experiments, writing, and interactive pages on knowledge editing and interpretability — what a model believes and how to tell whether a change took hold."
    >
      <div className="ocl-home">
        <Profile />

        <header className="ocl-home__hero">
          <div className="ocl-home__masthead">
            <p className="ocl-home__eyebrow">
              <span className="ocl-home__wave" aria-hidden="true">✦</span> What this lab is for
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
              <Jump to="/someday" name="someday" label="Someday" />
            </nav>
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
            <Note
              to="/labs"
              tone="sage"
              label={`Labs · ${labs.done} solved · ${labs.built - labs.done} ready to solve`}
            >
              {lastLab ? `Last solved: ${lastLab.title}` : "Not started"}
              <Bar done={labs.done} built={labs.built} total={labs.total} />
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
              <span className="ocl-home__of"> / {labs.built} built</span>
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

        <BuiltShowcase built={built} recent={recentBuilt} />

        <Band
          id="labs-heading"
          tone="sage"
          kicker="Labs · deployment and security"
          title={<><CountUp value={labs.built} /> labs built, <CountUp value={labs.done} /> solved</>}
          lede={`Each lab is a real kind of incident, broken on purpose and small enough to run on a laptop. I fix it, prove the fix, and write down what it taught. ${labs.built} of the ${labs.total} scenarios have a lab so far; the dark part of each bar is solved, the light part is built and waiting.`}
          href="/labs"
          cta="The full checklist →"
        >
          <Steps steps={LAB_LOOP} label="What every lab asks" />
          <div className="ocl-home__labs">
            <ul className="ocl-home__tracks">
              {labs.tracks.map((t) => (
                <li key={t.id}>
                  <Link to={`/labs#track-${t.id}`} className="ocl-home__track">
                    <TrackThumb id={t.id} />
                    <span className="ocl-home__trackName">{t.title}</span>
                    <span className="ocl-home__trackCount">
                      {t.done} solved · {t.built - t.done} ready · {t.total}
                    </span>
                    <Bar done={t.done} built={t.built} total={t.total} />
                  </Link>
                </li>
              ))}
            </ul>
            <div className="ocl-home__solved">
              <p className="ocl-home__solvedLabel">Solved so far</p>
              {labs.solved.length > 0 ? (
                <ol className="ocl-solved">
                  {labs.solved.slice(0, 5).map((s) => (
                    <li key={s.title} className="ocl-solved__item">
                      <span className="ocl-solved__tick" aria-hidden="true">✓</span>
                      <span className="ocl-solved__what">
                        {s.href ? (
                          <a href={s.href} target="_blank" rel="noreferrer">
                            {s.title}
                          </a>
                        ) : (
                          s.title
                        )}
                        <span className="ocl-solved__section">{s.section}</span>
                      </span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="ocl-home__empty">None yet.</p>
              )}
              <Link className="ocl-home__more" to="/notebook/opz/">
                What each one taught →
              </Link>
              {labs.ready.length > 0 ? (
                <>
                  <p className="ocl-home__solvedLabel ocl-home__readyLabel">
                    Built, ready to solve · {labs.ready.length}
                  </p>
                  <ol className="ocl-solved">
                    {labs.ready.slice(0, 5).map((r) => (
                      <li key={r.number} className="ocl-solved__item">
                        <span className="ocl-solved__tick ocl-solved__tick--ready" aria-hidden="true">
                          {r.number}
                        </span>
                        <span className="ocl-solved__what">
                          <a href={r.href} target="_blank" rel="noreferrer">
                            {r.title}
                          </a>
                          <span className="ocl-solved__section">{r.section}</span>
                        </span>
                      </li>
                    ))}
                  </ol>
                  <Link className="ocl-home__more" to="/labs">
                    All {labs.ready.length} waiting →
                  </Link>
                </>
              ) : null}
            </div>
          </div>
        </Band>

        <Band
          id="agentic-heading"
          tone="lilac"
          kicker="Agentic · the work that runs overnight"
          title={<>The tools that run overnight, and the rules they run by</>}
          lede="Experiments run while I sleep. These are the small tools that queue them, refuse the unsafe ones, sort the failures and leave a report, so in the morning only the one thing that needs a person is waiting for me. Underneath them is one file of instructions every AI session here starts from."
          href="/agentic"
          cta="How it all fits →"
        >
          <Steps steps={AGENT_FLOW} label="One night of unattended work" />
          <div className="ocl-home__agents">
            {AGENTIC.map((item: Agentic) => (
              <AgenticCard
                key={item.name}
                name={item.name}
                href={`/agentic/${item.name}`}
                title={item.title}
                blurb={item.blurb}
                sample={item.sample}
                meta={item.where}
              />
            ))}
            <AgenticCard
              name="practice"
              href="/agentic/practice"
              title="The practice, and its limits"
              blurb={
                "The boundary between what a loop may own and what a person must, and an " +
                "honest account of what none of it can catch."
              }
              sample={"A green harness is not a\nsound experiment.\n\nE-036 passed every gate\nand still measured two of\nsix criteria in ways that\ncould not answer their own\nquestions."}
            />
            {GUIDES.map((item: Guide) => (
              <AgenticCard
                key={item.name}
                name={item.name}
                href={item.href}
                external
                title={item.title}
                blurb={item.blurb}
                sample={item.sample}
                meta={item.file}
              />
            ))}
          </div>
        </Band>

        <Band
          id="reading-heading"
          tone="gold"
          kicker="Reading · before the next experiment"
          title={<><CountUp value={read} /> read, {papers.length} on the list</>}
          lede={
            <>
              The papers my work rests on, and why each one matters to it. A
              citation counts as checked only once I have read it against the
              paper itself
              {unchecked.length === 0
                ? ", and every one on the list has been."
                : `; ${unchecked.length} on the list still have not.`}
            </>
          }
          href="/reading"
          cta="The reading list →"
        >
          {nextUp.length > 0 ? (
            <ol className="ocl-paper-cards">
              {nextUp.map((paper, i) => (
                <li key={paper.id} className="ocl-paper-card__card" style={{ rotate: `${[-0.6, 0.5, -0.3, 0.7][i % 4]}deg` }}>
                  <span className="ocl-paper-card__n">Up next · {String(i + 1).padStart(2, "0")}</span>
                  <Link className="ocl-paper-card__title" to={`/reading#${paper.id}`}>{paper.title}</Link>
                  <span className="ocl-paper-card__by">
                    {firstAuthor(paper.authors)} · {paper.year}
                    {paper.venue ? ` · ${paper.venue}` : ""}
                  </span>
                  {paper.gives_me ? (
                    <span className="ocl-paper-card__why">
                      <b>Why I'm reading it</b> {paper.gives_me}
                    </span>
                  ) : null}
                  <span className={`ocl-paper-card__check${paper.verified ? " is-checked" : ""}`}>
                    {paper.verified ? "✓ citation checked" : "○ citation not yet checked"}
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="ocl-home__empty">Nothing marked next up.</p>
          )}
        </Band>

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
