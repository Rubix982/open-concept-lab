import { useEffect, useState, type ReactNode } from "react";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
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

type Progress = "all" | "todo" | "done";
type Kind = "all" | "lab" | "build" | "design" | "cloud";

const KINDS: { id: Kind; label: string; title: string }[] = [
  { id: "all", label: "Any kind", title: "Every line" },
  { id: "lab", label: "Lab", title: "Break it, fix it, prove it with check.sh — local and free" },
  { id: "build", label: "Build", title: "Build it from scratch, then a harness injects the failure" },
  { id: "design", label: "Design", title: "Nothing to break: a one-page decision record" },
  { id: "cloud", label: "Cloud", title: "Needs a real AWS or Azure account" },
];

function kindOf(item: ChecklistItem): Kind {
  if (item.tags.includes("cloud")) return "cloud";
  if (item.tags.includes("design")) return "design";
  if (item.tags.includes("build")) return "build";
  return "lab";
}

function count(items: ChecklistItem[]): { done: number; total: number } {
  return { done: items.filter((i) => i.done).length, total: items.length };
}

function Bar({ done, total }: { done: number; total: number }): ReactNode {
  return (
    <span className="ocl-labs__bar" aria-hidden="true">
      <span style={{ width: `${total ? (done / total) * 100 : 0}%` }} />
    </span>
  );
}

function Item({ item }: { item: ChecklistItem }): ReactNode {
  const kind = kindOf(item);
  return (
    <li className={`ocl-labs__item${item.done ? " is-done" : ""}`}>
      <span className="ocl-labs__mark" aria-label={item.done ? "done" : "not done"}>
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
    <div className={`ocl-labs__section${open ? " is-open" : ""}`} id={section.id}>
      <h3 className="ocl-labs__sectionTitle">
        <button type="button" aria-expanded={open} onClick={onToggle}>
          <span className="ocl-labs__chev" aria-hidden="true">{open ? "▾" : "▸"}</span>
          <span className="ocl-labs__sectionName">{section.title}</span>
          <span className="ocl-labs__count">
            {shown.length < section.items.length ? `${shown.length} match · ` : ""}
            {c.done} / {c.total}
            <Bar {...c} />
          </span>
        </button>
      </h3>
      {open ? (
        <>
          {section.note ? (
            <p className="ocl-labs__note" dangerouslySetInnerHTML={{ __html: section.note }} />
          ) : null}
          <ul className="ocl-labs__list">
            {shown.map((item) => (
              <Item key={item.title} item={item} />
            ))}
          </ul>
        </>
      ) : null}
    </div>
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
    (progress === "all" || (progress === "done") === item.done) &&
    (kind === "all" || kindOf(item) === kind) &&
    (q === "" || textOf(item).includes(q));
  const shown = items.filter(keep).length;

  // a link to /labs#c4 lands on that section, opened
  useEffect(() => {
    if (window.matchMedia("(max-width: 996px)").matches) setNavOpen(false);
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
      <div className="ocl-page ocl-labs">
        <header className="ocl-page__head">
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
              <dt>Done</dt>
              <dd className="ocl-labs__done">{totals.done}</dd>
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
                              <span className={sc.done ? "ocl-labs__navDone" : undefined}>
                                {filtering ? matches : `${sc.done}/${sc.total}`}
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
                {(["all", "todo", "done"] as Progress[]).map((p) => (
                  <button
                    key={p}
                    type="button"
                    className={`ocl-labs__filter${progress === p ? " is-active" : ""}`}
                    aria-pressed={progress === p}
                    onClick={() => setProgress(p)}
                  >
                    {p === "all" ? "All" : p === "todo" ? "To do" : "Done"}
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
                    <span className="ocl-labs__count">
                      {tc.done} / {tc.total}
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
                <code>projects/opz/labs/CHECKLIST.md</code>
              </a>{" "}
              at build time; ticking a line there ticks it here. Where several of
              my original scenarios were the same exercise, they share a line and
              are listed under “Also covers”.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
