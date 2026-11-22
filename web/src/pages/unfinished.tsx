import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Unfinished, UnfinishedActivity } from "@site/plugins/lab-data";
import PageArt from "@site/src/components/PageArt";

/** "May 2025", in UTC so the build and the browser agree. */
function monthName(ym: string, style: "short" | "long" = "short"): string {
  return new Intl.DateTimeFormat("en-GB", { month: style, year: "numeric", timeZone: "UTC" }).format(
    new Date(`${ym}-01T00:00:00Z`),
  );
}

function day(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(`${iso}T00:00:00Z`),
  );
}

/** Every YYYY-MM from `from` to `to`, inclusive. */
function monthsBetween(from: string, to: string): string[] {
  const out: string[] = [];
  let [y, m] = from.split("-").map(Number);
  const [ty, tm] = to.split("-").map(Number);
  while (y < ty || (y === ty && m <= tm)) {
    out.push(`${y}-${String(m).padStart(2, "0")}`);
    m += 1;
    if (m > 12) {
      m = 1;
      y += 1;
    }
  }
  return out;
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** "8 months", "1 year", "2 years, 3 months". */
function span(months: number): string {
  if (months < 12) return plural(months, "month");
  const years = Math.floor(months / 12);
  const rest = months % 12;
  return rest ? `${plural(years, "year")}, ${plural(rest, "month")}` : plural(years, "year");
}

/**
 * Commits per month while the project was alive, then a dashed line for the
 * time since. The quiet stretch is drawn at a fixed share of the width rather
 * than to scale, so a project from 2019 still shows its working months.
 */
function Strip({ activity, now }: { activity: UnfinishedActivity; now: string }): ReactNode {
  const first = activity.first.slice(0, 7);
  const last = activity.last.slice(0, 7);
  const months = monthsBetween(first, last);
  const peak = Math.max(...Object.values(activity.months));
  const quiet = Math.max(0, monthsBetween(last, now).length - 1);
  const summary =
    `${plural(activity.commits, "commit")} between ${monthName(first, "long")} and ${monthName(last, "long")}` +
    (quiet ? `, then none for ${span(quiet)}` : "");

  return (
    <div className="ocl-unf__strip" role="img" aria-label={summary}>
      <div className="ocl-unf__active" style={{ ["--ocl-unf-n" as string]: months.length }}>
        <div className="ocl-unf__bars">
          {months.map((ym) => {
            const n = activity.months[ym] ?? 0;
            return (
              <span key={ym} className="ocl-unf__month" data-tip={`${monthName(ym)} · ${plural(n, "commit")}`}>
                {n ? <i style={{ height: `${Math.max(8, (n / peak) * 100)}%` }} /> : null}
              </span>
            );
          })}
        </div>
        <div className="ocl-unf__ends" aria-hidden="true">
          <span>{monthName(first)}</span>
          {months.length > 1 ? <span>{monthName(last)}</span> : null}
        </div>
      </div>
      {quiet ? (
        <div className="ocl-unf__quiet" aria-hidden="true">
          <div className="ocl-unf__dash">
            <span>quiet for {span(quiet)}</span>
          </div>
          <div className="ocl-unf__ends">
            <span />
            <span>{monthName(now)}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Card({ entry, now, tone }: { entry: Unfinished; now: string; tone: number }): ReactNode {
  const external = entry.carried && /^https?:/.test(entry.carried.to);
  return (
    <article id={entry.name} className={`ocl-unf__card ocl-window--tone${tone}`}>
      <header className="ocl-unf__head">
        <div className="ocl-unf__name">
          <h2 className="ocl-unf__title">
            <a href={`#${entry.name}`}>{entry.title}</a>
          </h2>
          <p className="ocl-unf__what">{entry.what}</p>
          {entry.stack ? <p className="ocl-unf__stack">{entry.stack}</p> : null}
        </div>
        {entry.activity ? <Strip activity={entry.activity} now={now} /> : null}
      </header>

      <div className="ocl-unf__cols">
        <section>
          <h3 className="ocl-unf__label">What I thought it would be</h3>
          <p>{entry.thought}</p>
        </section>
        {entry.got ? (
          <section>
            <h3 className="ocl-unf__label">How far it got</h3>
            <p>{entry.got}</p>
          </section>
        ) : null}
        {entry.stopped ? (
          <section>
            <h3 className="ocl-unf__label">Why it stopped</h3>
            <p>{entry.stopped}</p>
          </section>
        ) : null}
      </div>

      {entry.repo || entry.carried ? (
        <footer className="ocl-unf__foot">
          {entry.repo ? (
            <a href={`https://github.com/${entry.repo}`} target="_blank" rel="noreferrer">
              github.com/{entry.repo} ↗
            </a>
          ) : null}
          {entry.carried ? (
            external ? (
              <a href={entry.carried.to} target="_blank" rel="noreferrer">
                {entry.carried.label} ↗
              </a>
            ) : (
              <Link to={entry.carried.to}>{entry.carried.label} →</Link>
            )
          ) : null}
        </footer>
      ) : null}
    </article>
  );
}

export default function UnfinishedPage(): ReactNode {
  const { unfinished, builtAt } = usePluginData("ocl-lab-data") as LabData;
  const now = builtAt.slice(0, 7);
  // newest start first; one never fetched keeps its place in the file, after the rest
  const shown = unfinished
    .map((entry, i) => ({ entry, i }))
    .sort(
      (a, b) =>
        (b.entry.activity?.first ?? "").localeCompare(a.entry.activity?.first ?? "") || a.i - b.i,
    )
    .map(({ entry }) => entry);
  const fetched = unfinished
    .map((e) => e.activity?.fetched)
    .filter(Boolean)
    .sort()
    .at(0);

  return (
    <Layout
      title="Unfinished"
      description="Projects I started because I was sure something needed to exist, and stopped partway, with how far each got and how long it has been quiet."
    >
      <div className="ocl-page">
        <header className="ocl-showcase ocl-built__hero ocl-unf__hero">
          <div>
            <p className="ocl-showcase__kicker">Unfinished · started, and stopped partway</p>
            <h1 className="ocl-showcase__title">
              {unfinished.length} {unfinished.length === 1 ? "project" : "projects"} I started and never finished
            </h1>
            <p className="ocl-showcase__lede">
              Each one began because I was sure something needed to exist, and
              stopped somewhere in the middle. The bars are commits per month,
              read from GitHub, and the dashed line is the time since the last one.
            </p>
          </div>
          <PageArt name="unfinished" />
        </header>

        <div className="ocl-unf__list">
          {shown.map((entry, i) => (
            <Card key={entry.name} entry={entry} now={now} tone={((i + 2) % 6) + 1} />
          ))}
        </div>
        {!shown.length && <p className="ocl-page__note">Nothing here yet.</p>}

        <p className="ocl-page__foot">
          Kept in <code>data/unfinished.yml</code>. <code>npm run unfinished</code>{" "}
          reads each repo's commits from GitHub into{" "}
          <code>data/unfinished-activity.json</code>
          {fetched ? `, last on ${day(fetched)}` : ""}.
        </p>
      </div>
    </Layout>
  );
}
