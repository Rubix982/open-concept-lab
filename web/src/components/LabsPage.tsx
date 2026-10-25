import { useEffect, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import PageArt from "@site/src/components/PageArt";
import useBaseUrl from "@docusaurus/useBaseUrl";
import Flow from "@site/src/components/visual/Flow";
import type {
  Checklist,
  ChecklistItem,
  ChecklistSection,
} from "@site/plugins/lab-data";

/** Plain lower-cased text of an entry, for search. */
const searchText = new WeakMap<ChecklistItem, string>();
function textOf(item: ChecklistItem): string {
  let text = searchText.get(item);
  if (text === undefined) {
    text = [item.title, item.rest, ...item.fields.map((f) => f.html)]
      .join(" ")
      .replace(/<[^>]+>/g, "")
      .replace(/&amp;/g, "&")
      .toLowerCase();
    searchText.set(item, text);
  }
  return text;
}

type Progress = "all" | "solved" | "built" | "planned";

const PROGRESS: { id: Progress; label: string; title: string }[] = [
  { id: "all", label: "All", title: "Every line" },
  { id: "solved", label: "Solved", title: "Fixed, proven with check.sh, retro written" },
  { id: "built", label: "Ready to solve", title: "The lab is built and waiting: broken system, hints, check.sh" },
  { id: "planned", label: "Not built yet", title: "On the list; no lab folder yet" },
];

const STATUS_LABEL: Record<ChecklistItem["status"], string> = {
  solved: "solved",
  built: "ready to solve",
  planned: "not built yet",
};
type Kind = "all" | "lab" | "build" | "design" | "cloud";

const KINDS: { id: Kind; label: string; title: string }[] = [
  { id: "all", label: "Any kind", title: "Every line" },
  { id: "lab", label: "Lab", title: "Break it, fix it, prove it with check.sh — local and free" },
  { id: "build", label: "Build", title: "Build it from scratch, then a harness injects the failure" },
  { id: "design", label: "Design", title: "Nothing to break: a one-page decision record" },
  { id: "cloud", label: "Cloud", title: "Cloud scenarios; the built ones run on local emulators (MinIO, moto), no account needed" },
];

function kindOf(item: ChecklistItem): Kind {
  if (item.tags.includes("cloud")) return "cloud";
  if (item.tags.includes("design")) return "design";
  if (item.tags.includes("build")) return "build";
  return "lab";
}

type Counts = { done: number; built: number; total: number };

/** done = solved; built = has a lab, solved or not. */
function count(items: ChecklistItem[]): Counts {
  return {
    done: items.filter((i) => i.done).length,
    built: items.filter((i) => i.status !== "planned").length,
    total: items.length,
  };
}

function Bar({ done, built, total }: Counts): ReactNode {
  const pct = (n: number) => `${total ? (n / total) * 100 : 0}%`;
  return (
    <span className="ocl-labs__bar" aria-hidden="true">
      <span className="ocl-labs__barSolved" style={{ width: pct(done) }} />
      <span className="ocl-labs__barBuilt" style={{ width: pct(built - done) }} />
    </span>
  );
}

/** "4 solved · 30 ready · 244" in words, for titles and screen readers. */
function describe({ done, built, total }: Counts): string {
  return `${done} solved, ${built - done} ready to solve, ${total - built} not built yet`;
}

function Item({ item }: { item: ChecklistItem }): ReactNode {
  const kind = kindOf(item);
  return (
    <li className={`ocl-labs__item is-${item.status}${item.done ? " is-done" : ""}`}>
      <span className="ocl-labs__mark" aria-label={STATUS_LABEL[item.status]} title={STATUS_LABEL[item.status]}>
        {item.done ? "✓" : ""}
      </span>
      <div className="ocl-labs__body">
        <p className="ocl-labs__head">
          <span className="ocl-labs__title">{item.title}</span>
          {kind !== "lab" ? (
            <span className={`ocl-pill ocl-labs__kind ocl-labs__kind--${kind}`}>{kind}</span>
          ) : null}
          {item.rest ? (
            <span className="ocl-labs__rest" dangerouslySetInnerHTML={{ __html: item.rest }} />
          ) : null}
          {item.lab ? (
            <a
              className={`ocl-labs__lab ocl-labs__lab--${item.status}`}
              href={item.lab.href}
              target="_blank"
              rel="noreferrer"
            >
              Lab {item.lab.number} · {STATUS_LABEL[item.status]} ↗
            </a>
          ) : null}
        </p>
        {item.fields.length > 0 ? (
          <dl className="ocl-labs__fields">
            {item.fields.map((f) => (
              <div key={f.label}>
                <dt>{f.label}</dt>
                <dd dangerouslySetInnerHTML={{ __html: f.html }} />
              </div>
            ))}
          </dl>
        ) : null}
      </div>
    </li>
  );
}

function Section({
  section,
  shown,
  open,
  onToggle,
}: {
  section: ChecklistSection;
  shown: ChecklistItem[];
  open: boolean;
  onToggle: () => void;
}): ReactNode {
  const c = count(section.items);
  return (
    <div className={`ocl-labs__section${open ? " is-open" : ""}`}>
      <h3 className="ocl-labs__sectionTitle" id={section.id}>
        <button type="button" aria-expanded={open} onClick={onToggle}>
          <span className="ocl-labs__chev" aria-hidden="true">{open ? "▾" : "▸"}</span>
          <span className="ocl-labs__sectionName">{section.title}</span>
          <span className="ocl-labs__count">
            {shown.length < section.items.length ? `${shown.length} match · ` : ""}
            <span title={describe(c)}>
              {c.done} / {c.built} / {c.total}
            </span>
            <Bar {...c} />
          </span>
        </button>
      </h3>
      {/* closed sections stay in the page, hidden, so site search and the
          browser's find can still reach every line */}
      <div hidden={!open}>
        {section.note ? (
          <p className="ocl-labs__note" dangerouslySetInnerHTML={{ __html: section.note }} />
        ) : null}
        <ul className="ocl-labs__list">
          {shown.map((item) => (
            <Item key={item.title} item={item} />
          ))}
        </ul>
      </div>
    </div>
  );
}

/** The five moves every lab makes, from the page's own description. */
const LOOP = [
  { art: "lab-break", title: "Break it", text: "A real incident, shrunk to something that runs on a laptop." },
  { art: "lab-diagnose", title: "Diagnose it", text: "Find the cause from the symptoms, not from the answer." },
  { art: "lab-fix", title: "Fix it", text: "The smallest change that removes the cause." },
  { art: "lab-prove", title: "Prove it", text: "A <code>check.sh</code> that fails on a cover-up, not only on the bug." },
  { art: "lab-retro", title: "Write it down", text: "A five-line retro: what broke, why, what it taught." },
];

/** A progress ring: the share of a track's lines that are done. */
function Ring({ done, built, total }: Counts): ReactNode {
  const r = 22;
  const c = 2 * Math.PI * r;
  const share = total ? done / total : 0;
  const builtShare = total ? built / total : 0;
  return (
    <svg className="ocl-ring" viewBox="0 0 56 56" width="56" height="56" aria-hidden="true">
      <circle cx="28" cy="28" r={r} className="ocl-ring__track" />
      <circle
        cx="28"
        cy="28"
        r={r}
        className="ocl-ring__built"
        style={{ strokeDasharray: `${Math.max(builtShare * c, built ? 2 : 0)} ${c}` }}
      />
      <circle
        cx="28"
        cy="28"
        r={r}
        className="ocl-ring__done"
        style={{ strokeDasharray: `${Math.max(share * c, done ? 2 : 0)} ${c}` }}
      />
      <text x="28" y="32" textAnchor="middle" className="ocl-ring__label">
        {Math.round(builtShare * 100)}%
      </text>
    </svg>
  );
}

function TrackCard({
  id,
  title,
  counts,
  onJump,
}: {
  id: string;
  title: string;
  counts: Counts;
  onJump: () => void;
}): ReactNode {
  const { done, built, total } = counts;
  const art = useBaseUrl(`/img/art/tracks/${id}.svg`);
  const [code, name] = title.replace(/^Track /, "").split(" · ");
  return (
    <a
      className="ocl-track"
      href={`#track-${id}`}
      onClick={(e) => {
        e.preventDefault();
        onJump();
      }}
    >
      <img className="ocl-track__art" src={art} alt="" loading="lazy" decoding="async" />
      <span className="ocl-track__body">
        <span className="ocl-track__code">Track {code}</span>
        <span className="ocl-track__name">{(name ?? title).replace(/\s*`?\[.*$/, "").replace(/\s*\(.*\)$/, "")}</span>
        <span className="ocl-track__count">
          {done} solved · {built - done} ready · {total - built} not built
        </span>
      </span>
      <Ring {...counts} />
    </a>
  );
}

/**
 * Every line of the checklist as one square, grouped by track, filled when
 * done. The finished ones also appear as stamps underneath.
 */
function Field({ checklist, onJump }: { checklist: Checklist; onJump: (id: string) => void }): ReactNode {
  const solved = checklist.tracks.flatMap((t) =>
    t.sections.flatMap((s) => s.items.filter((i) => i.done).map((i) => ({ item: i, section: s }))),
  );
  const ready = checklist.tracks
    .flatMap((t) =>
      t.sections.flatMap((s) =>
        s.items.filter((i) => i.status === "built" && i.lab).map((i) => ({ item: i, section: s, track: t.id })),
      ),
    )
    .sort((a, b) => Number(a.item.lab!.number) - Number(b.item.lab!.number));
  return (
    <section className="ocl-page__section ocl-field" aria-label="Every line of the checklist">
      <h2 className="ocl-page__sectionTitle">Every line, one square</h2>
      <ul className="ocl-field__legend" aria-label="Legend">
        <li><span className="ocl-field__cell is-solved is-done" aria-hidden="true" /> Solved</li>
        <li><span className="ocl-field__cell is-built" aria-hidden="true" /> Built, ready to solve</li>
        <li><span className="ocl-field__cell is-planned" aria-hidden="true" /> Not built yet</li>
      </ul>
      <div className="ocl-field__tracks">
        {checklist.tracks.map((t) => (
          <div key={t.id} className={`ocl-field__track ocl-field__track--${t.id}`}>
            <p className="ocl-field__label">{t.id.toUpperCase()}</p>
            <div className="ocl-field__grid">
              {t.sections.flatMap((s) =>
                s.items.map((item) => (
                  <a
                    key={`${s.id}-${item.title}`}
                    href={`#${s.id}`}
                    className={`ocl-field__cell is-${item.status}${item.done ? " is-done" : ""}`}
                    title={`${s.title.replace(/\s*\(.*\)$/, "")} — ${item.title}${item.lab ? ` (lab ${item.lab.number}, ${STATUS_LABEL[item.status]})` : ""}`}
                    aria-label={`${item.title}, ${STATUS_LABEL[item.status]}`}
                    onClick={(e) => {
                      e.preventDefault();
                      onJump(s.id);
                    }}
                  />
                )),
              )}
            </div>
          </div>
        ))}
      </div>
      {solved.length > 0 ? (
        <div className="ocl-stamps">
          {solved.map(({ item, section }) => (
            <a
              key={`${section.id}-${item.title}`}
              className="ocl-stamp"
              href={`#${section.id}`}
              onClick={(e) => {
                e.preventDefault();
                onJump(section.id);
              }}
            >
              <span className="ocl-stamp__code">{section.id.toUpperCase()}</span>
              <span className="ocl-stamp__title">{item.title}</span>
              <span className="ocl-stamp__seal" aria-hidden="true">✓</span>
            </a>
          ))}
        </div>
      ) : null}
      {ready.length > 0 ? (
        <div className="ocl-ready">
          <p className="ocl-ready__label">Built, ready to solve · {ready.length}</p>
          <ol className="ocl-ready__list">
            {ready.map(({ item, section, track }) => (
              <li key={item.lab!.number} className={`ocl-ready__item ocl-ready__item--${track}`}>
                <a href={item.lab!.href} target="_blank" rel="noreferrer">
                  <span className="ocl-ready__num">{item.lab!.number}</span>
                  <span className="ocl-ready__title">{item.title}</span>
                  <span className="ocl-ready__section">{section.id.toUpperCase()}</span>
                </a>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </section>
  );
}

export default function LabsPage({ checklist }: { checklist: Checklist }): ReactNode {
  const [progress, setProgress] = useState<Progress>("all");
  const [kind, setKind] = useState<Kind>("all");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [navOpen, setNavOpen] = useState(true);

  const sections = checklist.tracks.flatMap((t) => t.sections);
  const items = sections.flatMap((s) => s.items);
  const totals = count(items);

  const q = query.trim().toLowerCase();
  const filtering = progress !== "all" || kind !== "all" || q !== "";
  const keep = (item: ChecklistItem) =>
    (progress === "all" || item.status === progress) &&
    (kind === "all" || kindOf(item) === kind) &&
    (q === "" || textOf(item).includes(q));
  const shown = items.filter(keep).length;

  // a link to /labs#c4 lands on that section, opened
  useEffect(() => {
    if (window.matchMedia("(max-width: 996px)").matches) setNavOpen(false);
    // arriving from site search: carry the terms into this page's own filter
    const terms = new URLSearchParams(window.location.search).getAll("_highlight");
    if (terms.length > 0) setQuery(terms.join(" "));
    const id = window.location.hash.slice(1);
    if (sections.some((s) => s.id === id)) {
      setOpen(new Set([id]));
      requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView());
    }
  }, []);

  const toggle = (id: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const jump = (id: string) => {
    setOpen((prev) => new Set(prev).add(id));
    history.replaceState(null, "", `#${id}`);
    requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }));
  };

  // while filtering, every section with a match is shown open
  const isOpen = (id: string) => filtering || open.has(id);

  return (
    <Layout
      title="Labs"
      description="Deployment, DevOps and security, learned one small broken system at a time: every scenario as a checklist."
    >
      <main className="ocl-page ocl-labs">
        <header className="ocl-page__head ocl-page__head--art">
          <PageArt name="labs" />
          <h1 className="ocl-page__title">Labs</h1>
          <p className="ocl-page__lede">
            Every deployment and security scenario I want to have worked
            through, as one list. Each lab shrinks a real incident to something
            that runs on a laptop: break it, diagnose it, fix it, prove the fix
            with a check that fails on a cover-up, then write a five-line retro.
            The write-up of what each finished lab taught is in{" "}
            <Link to="/notebook/opz/">the notebook</Link>.
          </p>
          <dl className="ocl-tally">
            <div>
              <dt>Solved</dt>
              <dd className="ocl-labs__done">{totals.done}</dd>
            </div>
            <div>
              <dt>Ready to solve</dt>
              <dd className="ocl-labs__ready">{totals.built - totals.done}</dd>
            </div>
            <div>
              <dt>Not built yet</dt>
              <dd>{totals.total - totals.built}</dd>
            </div>
            <div>
              <dt>Lines</dt>
              <dd>{totals.total}</dd>
            </div>
            <div>
              <dt>Tracks</dt>
              <dd>{checklist.tracks.length}</dd>
            </div>
          </dl>
        </header>

        <section className="ocl-page__section ocl-labs__loop">
          <h2 className="ocl-page__sectionTitle">What every lab is</h2>
          <Flow steps={LOOP} loop label="The loop every lab follows: break, diagnose, fix, prove, write it down" />
        </section>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">The tracks</h2>
          <div className="ocl-tracks">
            {checklist.tracks.map((t) => {
              const c = count(t.sections.flatMap((s) => s.items));
              return (
                <TrackCard
                  key={t.id}
                  id={t.id}
                  title={t.title}
                  counts={c}
                  onJump={() => {
                    history.replaceState(null, "", `#track-${t.id}`);
                    document.getElementById(`track-${t.id}`)?.scrollIntoView({ behavior: "smooth" });
                  }}
                />
              );
            })}
          </div>
        </section>

        <Field checklist={checklist} onJump={(id) => jump(id)} />

        <div className="ocl-labs__layout">
          <nav className="ocl-labs__nav" aria-label="Sections">
            <details
              className="ocl-labs__navWrap"
              open={navOpen}
              onToggle={(e) => setNavOpen(e.currentTarget.open)}
            >
              <summary>Jump to a section</summary>
              {checklist.tracks.map((t) => {
                const c = count(t.sections.flatMap((s) => s.items));
                return (
                  <div key={t.id} className="ocl-labs__navTrack">
                    <p className="ocl-labs__navTrackTitle">
                      {t.title.replace(/^Track (\w+) · /, "$1 · ")}
                      <span>{c.done}/{c.total}</span>
                    </p>
                    <ul>
                      {t.sections.map((s) => {
                        const sc = count(s.items);
                        const matches = s.items.filter(keep).length;
                        return (
                          <li key={s.id} className={filtering && matches === 0 ? "is-empty" : undefined}>
                            <a
                              href={`#${s.id}`}
                              onClick={(e) => {
                                e.preventDefault();
                                jump(s.id);
                              }}
                            >
                              <span>{s.title.replace(/\s*\(.*\)$/, "")}</span>
                              <span
                                className={sc.done ? "ocl-labs__navDone" : sc.built ? "ocl-labs__navReady" : undefined}
                                title={filtering ? undefined : describe(sc)}
                              >
                                {filtering ? matches : `${sc.done}/${sc.built}/${sc.total}`}
                              </span>
                            </a>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </details>
          </nav>

          <div className="ocl-labs__main">
            <div className="ocl-labs__filters">
              <input
                type="search"
                className="ocl-labs__search"
                placeholder="Search scenarios, tools, concepts…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search the checklist"
              />
              <div role="group" aria-label="Progress">
                {PROGRESS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    title={p.title}
                    className={`ocl-labs__filter${progress === p.id ? " is-active" : ""}`}
                    aria-pressed={progress === p.id}
                    onClick={() => setProgress(p.id)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <div role="group" aria-label="Kind">
                {KINDS.map((k) => (
                  <button
                    key={k.id}
                    type="button"
                    title={k.title}
                    className={`ocl-labs__filter${kind === k.id ? " is-active" : ""}`}
                    aria-pressed={kind === k.id}
                    onClick={() => setKind(k.id)}
                  >
                    {k.label}
                  </button>
                ))}
              </div>
              <div className="ocl-labs__bulk">
                {filtering ? (
                  <span>{shown} of {totals.total} match</span>
                ) : (
                  <>
                    <button type="button" onClick={() => setOpen(new Set(sections.map((s) => s.id)))}>
                      Expand all
                    </button>
                    <button type="button" onClick={() => setOpen(new Set())}>
                      Collapse all
                    </button>
                  </>
                )}
              </div>
            </div>

            {checklist.tracks.map((track) => {
              const visible = track.sections
                .map((s) => ({ s, shown: s.items.filter(keep) }))
                .filter(({ shown }) => shown.length > 0);
              if (visible.length === 0) return null;
              const tc = count(track.sections.flatMap((s) => s.items));
              return (
                <section className="ocl-labs__track" id={`track-${track.id}`} key={track.id}>
                  <h2 className="ocl-page__sectionTitle ocl-labs__trackTitle">
                    <span>{track.title}</span>
                    <span className="ocl-labs__count" title={describe(tc)}>
                      {tc.done} / {tc.built} / {tc.total}
                      <Bar {...tc} />
                    </span>
                  </h2>
                  {track.note ? (
                    <p className="ocl-page__note" dangerouslySetInnerHTML={{ __html: track.note }} />
                  ) : null}
                  {visible.map(({ s, shown }) => (
                    <Section
                      key={s.id}
                      section={s}
                      shown={shown}
                      open={isOpen(s.id)}
                      onToggle={() => toggle(s.id)}
                    />
                  ))}
                </section>
              );
            })}

            {shown === 0 ? <p className="ocl-page__note">Nothing matches.</p> : null}

            <p className="ocl-page__foot">
              Generated from{" "}
              <a href={checklist.source} target="_blank" rel="noreferrer">
                <code>opz/labs/CHECKLIST.md</code>
              </a>{" "}
              at build time; ticking a line there ticks it here. Where several of
              my original scenarios were the same exercise, they share a line and
              are listed under “Also covers”.
            </p>
          </div>
        </div>
      </main>
    </Layout>
  );
}
