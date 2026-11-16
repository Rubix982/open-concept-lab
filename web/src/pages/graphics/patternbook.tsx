import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import {
  BLIND,
  BUILT,
  LIBRARY,
  PATTERNBOOK,
  PINNED,
  RUNS,
  pageHref,
  promptFile,
  repoFile,
  stillSrc,
  type Run,
  type RunPage,
} from "@site/src/data/patternbook";
import styles from "./patternbook.module.css";

// Every page an agent built in patternbook's tests, with what it was given and how the judge
// voted. The pages themselves are served from /demos/patternbook/runs/ (data/built.yml); the
// words on this page come from src/data/patternbook.ts, which is copied from CARD.md.

const anchor = (id: string): string => id.toLowerCase();

function Window({ page, run, small }: { page: RunPage; run: Run; small?: boolean }): ReactNode {
  const href = useBaseUrl(pageHref(page.file));
  const still = useBaseUrl(stillSrc(page));
  const unguided = run.id === "C-005" || /no guidance/i.test(page.given);
  return (
    <figure
      className={`ocl-card ocl-card--window ocl-window--tone${unguided ? 3 : 6} ${styles.window}`}
    >
      <div className="ocl-card__chrome">
        <span className="ocl-window__dots" aria-hidden="true"><i /><i /><i /></span>
        <span className="ocl-window__address" aria-hidden="true">runs/{page.file}</span>
        <a className="ocl-card__open" href={href} target="_blank" rel="noreferrer" aria-label={`Open ${run.id}, ${page.given}`}>
          Open ↗
        </a>
      </div>
      <div
        className="ocl-card__preview"
        style={{ aspectRatio: page.detail ? "2 / 1" : small ? "4 / 5" : "4 / 3" }}
      >
        <a href={href} target="_blank" rel="noreferrer" tabIndex={-1} aria-hidden="true">
          <img className="ocl-card__image" src={still} alt="" loading="lazy" decoding="async" />
        </a>
      </div>
      <figcaption className={styles.cap}>
        <p className={styles.given}>{page.given}</p>
        {page.swatch && (
          <p className={styles.swatches}>
            {page.swatch.map((hex) => (
              <span key={hex}>
                <i style={{ background: hex }} aria-hidden="true" />
                <code>{hex}</code>
              </span>
            ))}
          </p>
        )}
        {page.verdicts && run.questions && (
          <ul className={styles.verdicts}>
            {run.questions.map(([label], i) => (
              <li key={label} data-verdict={page.verdicts?.[i]}>
                {label}: <b>{page.verdicts?.[i]}</b>
              </li>
            ))}
          </ul>
        )}
        {page.words !== undefined && (
          <p className={styles.meta}>{page.words.toLocaleString("en-US")} words</p>
        )}
        {page.notes && <p className={styles.meta}>{page.notes}</p>}
        {page.detail && <p className={styles.meta}>{page.detail}</p>}
        {page.later && (
          <p className={styles.later}>
            <span>Later, in C-010, on what gives it away:</span> “{page.later}”
          </p>
        )}
        <p className={styles.links}>
          {run.made ? (
            <a href={repoFile(run.made)} target="_blank" rel="noreferrer">How it was made</a>
          ) : (
            <a href={promptFile(page.file)} target="_blank" rel="noreferrer">Prompt</a>
          )}
          {page.source && (
            <>
              {" · "}
              <a href={repoFile(page.source[1])} target="_blank" rel="noreferrer">{page.source[0]}</a>
            </>
          )}
        </p>
      </figcaption>
    </figure>
  );
}

function Traits({ traits, of }: { traits: [string, number][]; of: number }): ReactNode {
  return (
    <table className={styles.traits}>
      <caption>On how many of the {of} pages each trait appeared</caption>
      <tbody>
        {traits.map(([trait, n]) => (
          <tr key={trait}>
            <th scope="row">{trait}</th>
            <td>
              <span className={styles.dots} aria-hidden="true">
                {Array.from({ length: of }, (_, i) => (
                  <i key={i} data-on={i < n ? "" : undefined} />
                ))}
              </span>
              <span className={styles.count}>{n} of {of}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RunSection({ run }: { run: Run }): ReactNode {
  const gallery = run.layout === "gallery";
  const studio = useBaseUrl(PATTERNBOOK.studio);
  return (
    <section id={anchor(run.id)} className={styles.run} aria-labelledby={`${anchor(run.id)}-title`}>
      <header className={styles.runHead}>
        <span className={styles.id}>{run.id}</span>
        <h2 id={`${anchor(run.id)}-title`}>{run.title}</h2>
      </header>
      <p className={styles.question}>{run.question}</p>
      {run.brief && (
        <p className={styles.brief}>
          <span className={styles.label}>{run.made ? "Setup" : "Brief"}</span> {run.brief}
        </p>
      )}
      {run.studio && (
        <p className={styles.brief}>
          <a href={studio + run.studio[1]} target="_blank" rel="noreferrer">{run.studio[0]} ↗</a>
        </p>
      )}
      {run.questions && (
        <dl className={styles.asked}>
          {run.questions.map(([label, full]) => (
            <div key={label}>
              <dt className={styles.label}>{label}</dt>
              <dd>{full}</dd>
            </div>
          ))}
        </dl>
      )}
      {run.pages.length > 0 && (
        <div className={gallery ? styles.gallery : styles.pair}>
          {run.pages.map((p) => (
            <Window key={p.file} page={p} run={run} small={gallery} />
          ))}
        </div>
      )}
      {run.traits && <Traits traits={run.traits} of={run.pages.length} />}
      {run.judge && (
        <div className={styles.judge}>
          <p className={styles.label}>The judge</p>
          {run.judge.map((j) => (
            <p key={j}>{j}</p>
          ))}
        </div>
      )}
      <p className={styles.showed}>{run.showed}</p>
    </section>
  );
}

export default function Patternbook(): ReactNode {
  return (
    <Layout
      title="patternbook"
      description="Every page an AI agent built in patternbook's blind tests, with what it was given and how the judge voted."
    >
      <div className="ocl-page">
        <header className="ocl-page__head">
          <p className="ocl-page__kicker"><Link to="/graphics">Graphics</Link></p>
          <h1 className="ocl-page__title">patternbook</h1>
          <p className="ocl-page__lede">
            A library of design knowledge for coding agents, taken from human-made print and
            filed by the problem a page has to solve. Given no style, the agent behind these
            tests put seven pages on six unrelated subjects on the same cream paper with a
            terracotta accent. An entry in patternbook counts only after a page built from it
            wins a blind pick. These are all the pages from those picks, in the order the
            tests ran.
          </p>
          <p className="ocl-page__note">
            In most tests, two new agents get the same brief and different guidance. C-012 and
            C-013 keep one page and change only how its drawings are printed. The judge, who is
            also the author, sees the two pages unlabelled and in random order, and answers the
            questions before finding out which is which.
          </p>
          <dl className="ocl-tally">
            <div>
              <dt>Blind tests</dt>
              <dd>{BLIND.length}</dd>
            </div>
            <div>
              <dt>Pages built</dt>
              <dd>{BUILT}</dd>
            </div>
            <div>
              <dt>Problem entries</dt>
              <dd>{LIBRARY.problemEntries}</dd>
            </div>
            <div>
              <dt>Art styles</dt>
              <dd>{LIBRARY.artStyles}</dd>
            </div>
          </dl>
        </header>

        <nav className={styles.toc} aria-label="Tests on this page">
          <ol>
            {RUNS.map((r) => (
              <li key={r.id}>
                <a href={`#${anchor(r.id)}`}>
                  <span className={styles.id}>{r.id}</span> {r.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        {RUNS.map((r) => (
          <RunSection key={r.id} run={r} />
        ))}

        <section className="ocl-ag__sec ocl-ag__limit">
          <h2>What it can't show yet</h2>
          <p>
            Every test is one run per page, judged by one person, who is also the author and
            knew what each test was for. Every page came from one model, so C-005 measures this
            agent's default, not that of AI in general. The styles are written from print, and
            a web page isn't print: C-010 found that print's white space reads as cold on a
            screen. In C-012 and C-013 the judge had already seen the page being printed, and
            in C-014 the engine's pictures gave away which page used it.
          </p>
        </section>

        <p className="ocl-page__foot">
          Source: <a href={PATTERNBOOK.repo} target="_blank" rel="noreferrer">github.com/Rubix982/patternbook</a>,
          at commit <code>{PINNED.commit}</code>. Tests C-001 to {PINNED.last}, run on {PINNED.dates}.
          The pages open exactly as they were judged.
        </p>
      </div>
    </Layout>
  );
}
