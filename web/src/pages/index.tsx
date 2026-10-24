import type { ReactNode } from "react";
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

function SectionHead({
  title,
  href,
  linkLabel,
  kicker,
}: {
  title: string;
  href: string;
  linkLabel: string;
  kicker?: string;
}): ReactNode {
  return (
    <div className="ocl-home__sectionHead">
      <h2 className="ocl-home__sectionTitle">
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
            <p className="ocl-home__eyebrow">Open Concept Lab · Saif Ul Islam</p>
            <h1 className="ocl-home__title">
              What a model believes, and how to tell when it changes.
            </h1>
            <p className="ocl-home__blurb">
              Experiments, writing, and interactive pages I built to understand
              something. Most of what is here is provisional and says so, and the
              reading list marks which citations I have actually checked.
            </p>
            <nav className="ocl-home__jump" aria-label="Sections">
              <Link to="/writing">Writing</Link>
              <Link to="/notebook">Notebook</Link>
              <Link to="/labs">Labs</Link>
              <Link to="/reading">Reading</Link>
              <Link to="/agentic">Agentic</Link>
              <Link to="/shipped">Shipped</Link>
              <Link to="/built">Built</Link>
              <Link to="/about">About</Link>
              <a className="ocl-home__jumpOut" href="https://www.linkedin.com/in/suislam" target="_blank" rel="noreferrer">
                LinkedIn ↗
              </a>
              <a className="ocl-home__jumpOut" href="https://github.com/Rubix982" target="_blank" rel="noreferrer">
                GitHub ↗
              </a>
            </nav>
          </div>

          <aside className="ocl-home__now" aria-label="What is moving now">
            <p className="ocl-home__nowLabel">Now</p>
            {latest ? (
              <Link className="ocl-home__nowRow" to={latest.permalink}>
                <span className="ocl-home__nowKey">Latest writing · {shortDate(latest.date)}</span>
                <span className="ocl-home__nowValue">{latest.title}</span>
              </Link>
            ) : null}
            {active ? (
              <Link className="ocl-home__nowRow" to={active.notebook}>
                <span className="ocl-home__nowKey">Most recent plan · {active.name}</span>
                <span className="ocl-home__nowValue">{active.phase}</span>
              </Link>
            ) : null}
            <Link className="ocl-home__nowRow" to="/labs">
              <span className="ocl-home__nowKey">
                Labs · {labs.done} of {labs.total}
              </span>
              <span className="ocl-home__nowValue">
                {lastLab ? `Last solved: ${lastLab.title}` : "Not started"}
              </span>
              <Bar done={labs.done} total={labs.total} />
            </Link>
            {nextUp[0] ? (
              <Link className="ocl-home__nowRow" to={`/reading#${nextUp[0].id}`}>
                <span className="ocl-home__nowKey">Reading next</span>
                <span className="ocl-home__nowValue">{nextUp[0].title}</span>
              </Link>
            ) : null}
          </aside>
        </header>

        <dl className="ocl-home__stats">
          <div>
            <dt>Projects</dt>
            <dd>{projects.length}</dd>
          </div>
          <div>
            <dt>Pieces of writing</dt>
            <dd>{writing.length}</dd>
          </div>
          <div>
            <dt>Interactive pages</dt>
            <dd>{built.length}</dd>
          </div>
          <div>
            <dt>Papers read</dt>
            <dd>
              {read}
              <span className="ocl-home__of"> / {papers.length}</span>
            </dd>
          </div>
          <div>
            <dt>Labs solved</dt>
            <dd>
              {labs.done}
              <span className="ocl-home__of"> / {labs.total}</span>
            </dd>
          </div>
          <div>
            <dt>Citations unchecked</dt>
            <dd className={unchecked.length > 0 ? "ocl-tally--flag" : undefined}>{unchecked.length}</dd>
          </div>
        </dl>

        <section className="ocl-home__section">
          <SectionHead title="Projects" kicker="each one's status is read from its own plan" href="/notebook" linkLabel="Notebook" />
          <div className="ocl-home__projects">
            {projects.map((project) => (
              <ProjectCard key={project.name} project={project} />
            ))}
          </div>
        </section>

        <section className="ocl-home__section">
          <SectionHead title="Writing" href="/writing" linkLabel="All writing" />
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
            <SectionHead title="Reading next" href="/reading" linkLabel="Reading list" />
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
            <SectionHead title="Built" kicker="recently added" href="/built" linkLabel={`All ${built.length} pages`} />
            <div className="ocl-home__tiles">
              {recentBuilt.map((page) => (
                <BuiltTile key={page.name} page={page} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </Layout>
  );
}
