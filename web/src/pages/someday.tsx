import { useState, type ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, SomedayItem, SomedayKind, SomedayStatus } from "@site/plugins/lab-data";
import PageArt from "@site/src/components/PageArt";

const KINDS: { kind: SomedayKind; label: string; tone: string }[] = [
  { kind: "business", label: "Business", tone: "gold" },
  { kind: "try", label: "Try", tone: "pink" },
  { kind: "learn", label: "Learn", tone: "sage" },
  { kind: "make", label: "Make", tone: "lilac" },
];

const STATUSES: { status: SomedayStatus; title: string; note: string }[] = [
  { status: "spark", title: "Sparks", note: "Just written down. That is all they need to be." },
  { status: "exploring", title: "Exploring", note: "Being poked at, a little." },
  { status: "tried", title: "Tried", note: "Done once, to see." },
  { status: "project", title: "Became a project", note: "Graduated, with a link to where it went." },
  { status: "let-go", title: "Let go", note: "Kept, with the one line of why." },
];

const toneOf = (kind: SomedayKind) => KINDS.find((k) => k.kind === kind)?.tone ?? "pink";
const labelOf = (kind: SomedayKind) => KINDS.find((k) => k.kind === kind)?.label ?? kind;

/** "25 Oct 2026", in UTC so the build and the browser agree. */
function day(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(`${iso}T00:00:00Z`),
  );
}

function Idea({ item }: { item: SomedayItem }): ReactNode {
  const external = item.link && /^https?:/.test(item.link);
  // A note stays a note: the line, a short why, and a way into the longer
  // thinking, which lives on the idea's own page at reading width.
  return (
    <li className={`ocl-note ocl-note--${toneOf(item.kind)} ocl-someday__idea`}>
      <span className="ocl-note__tape" aria-hidden="true" />
      <span className="ocl-note__label">
        {labelOf(item.kind)} · {day(item.added)}
      </span>
      <span className="ocl-note__text">{item.what}</span>
      {item.why ? <span className="ocl-someday__why">{item.why}</span> : null}
      {item.note ? <span className="ocl-someday__why ocl-someday__letgo">Let go: {item.note}</span> : null}
      {item.words ? (
        <Link className="ocl-someday__link" to={`/someday/${item.slug}`}>
          Read the thinking → <span>{item.words} words</span>
        </Link>
      ) : null}
      {item.link ? (
        external ? (
          <a className="ocl-someday__link" href={item.link} target="_blank" rel="noreferrer">Where it went ↗</a>
        ) : (
          <Link className="ocl-someday__link" to={item.link}>Where it went →</Link>
        )
      ) : null}
    </li>
  );
}

export default function Someday(): ReactNode {
  const { someday } = usePluginData("ocl-lab-data") as LabData;
  const [kind, setKind] = useState<SomedayKind | "all">("all");
  const shown = someday
    .filter((item) => kind === "all" || item.kind === kind)
    // newest first; within a day, later in the file is newer
    .map((item, i) => ({ item, i }))
    .sort((a, b) => b.item.added.localeCompare(a.item.added) || b.i - a.i)
    .map(({ item }) => item);

  return (
    <Layout
      title="Someday"
      description="Things I want to do, try, learn or make someday — written down so my head can stop holding them."
    >
      <div className="ocl-page">
        <header className="ocl-showcase ocl-built__hero ocl-someday__hero">
          <div>
            <p className="ocl-showcase__kicker">Someday · a list so my head can stop holding it</p>
            <h1 className="ocl-showcase__title">
              {someday.length} {someday.length === 1 ? "thing" : "things"} I want to do someday
            </h1>
            <p className="ocl-showcase__lede">
              Not plans. Lines I no longer have to remember. Some might become a
              business or a project, most will not, and that is fine. When one
              graduates it links to where it went; the ones I let go stay up with
              a line of why.
            </p>
          </div>
          <PageArt name="someday" />
        </header>

        <nav className="ocl-someday__filter" aria-label="Filter by kind">
          <button type="button" aria-pressed={kind === "all"} onClick={() => setKind("all")}>
            All <span>{someday.length}</span>
          </button>
          {KINDS.map((k) => (
            <button
              key={k.kind}
              type="button"
              className={`ocl-someday__chip--${k.tone}`}
              aria-pressed={kind === k.kind}
              onClick={() => setKind(k.kind)}
            >
              {k.label} <span>{someday.filter((item) => item.kind === k.kind).length}</span>
            </button>
          ))}
        </nav>

        {STATUSES.map(({ status, title, note }) => {
          const items = shown.filter((item) => item.status === status);
          if (!items.length) return null;
          return (
            <section key={status} className="ocl-someday__group" aria-labelledby={`someday-${status}`}>
              <h2 id={`someday-${status}`} className="ocl-someday__groupTitle">
                {title} <span>{items.length}</span>
              </h2>
              <p className="ocl-page__note">{note}</p>
              <ol className="ocl-notes ocl-someday__board">
                {items.map((item) => (
                  <Idea key={item.slug} item={item} />
                ))}
              </ol>
            </section>
          );
        })}
        {!shown.length && <p className="ocl-page__note">Nothing of this kind yet.</p>}

        <aside className="ocl-someday__how">
          <p className="ocl-showcase__kicker">Writing one down</p>
          <pre>
            <code>{`npm run idea -- "the idea"
npm run idea -- "the idea" --kind business --why "because…"`}</code>
          </pre>
          <p>
            Each idea is a Markdown file in <code>web/someday/</code>, named like a
            journal entry, with its kind and status in the front matter. Anything
            written below the front matter shows up behind “Read more”. Moving
            one along is a one-word edit to its <code>status</code>.
          </p>
        </aside>
      </div>
    </Layout>
  );
}
