import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import Evidence, { useEvidence } from "@site/src/components/Evidence";
import type {
  LabData,
  Practice as PracticeData,
  PracticeItem,
  PracticeLesson,
} from "@site/plugins/lab-data";

/**
 * How this lab runs agents — the boundary, the practices, and the incident behind each
 * rule. Content lives in `data/practice.yml`; nothing is written here.
 *
 * Fields may carry inline <code>/<em>/<strong>, authored in the YAML rather than parsed
 * out of prose. The file is repo-local and hand-kept, the same trust level as the
 * checklist notes LabsPage renders the same way.
 */
function Html({
  html,
  as: Tag = "p",
  className,
}: {
  html: string;
  as?: "p" | "span" | "td" | "li" | "div";
  className?: string;
}): ReactNode {
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: html.trim() }} />;
}

/**
 * An evidence id that resolves renders as a link into the ledger; one the generated
 * evidence.yml has not caught up with renders as a plain id. The alternative — the
 * component's own "missing" styling — marks a dead reference in oxide, which would be a
 * false alarm for an id that is simply newer than the last regeneration.
 */
function RecordId({ id }: { id: string }): ReactNode {
  const record = useEvidence(id);
  return record ? <Evidence id={id} /> : <code className="ocl-practice__id">{id}</code>;
}

function Records({ ids }: { ids?: string[] }): ReactNode {
  if (!ids || ids.length === 0) {
    return null;
  }
  return (
    <span className="ocl-practice__records">
      {ids.map((id, i) => (
        <span key={id}>
          {i > 0 ? " · " : ""}
          <RecordId id={id} />
        </span>
      ))}
    </span>
  );
}

function Item({ item }: { item: PracticeItem }): ReactNode {
  return (
    <div className="ocl-practice__item">
      <h3 className="ocl-practice__itemTitle">
        {item.name}
        {item.kicker ? <span className="ocl-practice__kicker">{item.kicker}</span> : null}
      </h3>
      <Html className="ocl-practice__body" html={item.body} />
      <Records ids={item.record} />
    </div>
  );
}

function Lesson({ lesson, n }: { lesson: PracticeLesson; n: number }): ReactNode {
  return (
    <li className="ocl-practice__lesson">
      <span className="ocl-practice__lessonN" aria-hidden="true">
        {String(n).padStart(2, "0")}
      </span>
      <Html className="ocl-practice__lessonRule" html={lesson.rule} />
      <Html className="ocl-practice__lessonHow" html={lesson.incident} />
      <p className="ocl-practice__lessonCost">
        <span className="ocl-practice__lessonCostLabel">Cost</span>
        {lesson.cost}
        {lesson.check ? (
          <span className="ocl-practice__check" title="Checked mechanically, not merely read">
            checked by <code>{lesson.check}</code>
          </span>
        ) : null}
      </p>
      <Records ids={lesson.record} />
    </li>
  );
}

export default function Practice(): ReactNode {
  const { practice } = usePluginData("ocl-lab-data") as LabData & {
    practice?: PracticeData;
  };

  if (!practice) {
    return (
      <Layout title="Practice">
        <main className="ocl-page">
          <p className="ocl-page__note">
            <code>data/practice.yml</code> is missing.
          </p>
        </main>
      </Layout>
    );
  }

  const { boundary } = practice;

  return (
    <Layout
      title="Practice"
      description="How this lab runs agents: the loop owns execution, a person owns judgement — and the incident behind every rule."
    >
      <main className="ocl-page">
        <header className="ocl-page__head">
          <h1 className="ocl-page__title">Practice</h1>
          <p className="ocl-page__lede">{practice.lede}</p>
          <dl className="ocl-tally">
            <div>
              <dt>Rules earned</dt>
              <dd>{practice.lessons.length}</dd>
            </div>
            <div>
              <dt>Practices</dt>
              <dd>{practice.practices.length}</dd>
            </div>
            <div>
              <dt>Drift questions</dt>
              <dd>{practice.questions.length}</dd>
            </div>
            <div>
              <dt>Wake-up triggers</dt>
              <dd>{boundary.escalation.length}</dd>
            </div>
          </dl>
        </header>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">The boundary</h2>
          <p className="ocl-practice__rule">{boundary.rule}</p>
          <div className="ocl-practice__split">
            <div>
              <h3 className="ocl-practice__colTitle">It owns</h3>
              <ul className="ocl-practice__list">
                {boundary.owns.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="ocl-practice__colTitle ocl-practice__colTitle--no">
                It does not
              </h3>
              <ul className="ocl-practice__list ocl-practice__list--no">
                {boundary.refuses.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          </div>

          <p className="ocl-page__note">
            Each half comes from the record rather than from principle{" "}
            <Records ids={boundary.record} />
          </p>
          <ol className="ocl-practice__reasons">
            {boundary.reasons.map((reason, i) => (
              <li key={i}>
                <Html className="ocl-practice__body" html={reason.text} />
                <Records ids={reason.record} />
              </li>
            ))}
          </ol>

          <p className="ocl-practice__aside">{boundary.rejected}</p>

          <h3 className="ocl-practice__colTitle">It wakes someone for four things</h3>
          <div className="ocl-table__scroll">
            <table className="ocl-table">
              <thead>
                <tr>
                  <th>Trigger</th>
                  <th>Why it is worth waking for</th>
                </tr>
              </thead>
              <tbody>
                {boundary.escalation.map((row, i) => (
                  <tr key={i}>
                    <Html as="td" className="ocl-table__main" html={row.trigger} />
                    <Html as="td" html={row.why} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="ocl-page__note">{boundary.escalation_note}</p>
          <p className="ocl-practice__aside">{boundary.falsification}</p>
        </section>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">The practices</h2>
          {practice.practices.map((item) => (
            <Item key={item.name} item={item} />
          ))}
        </section>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">What it asks of the work</h2>
          <Html className="ocl-page__note" html={practice.questions_note} />
          <div className="ocl-table__scroll">
            <table className="ocl-table">
              <thead>
                <tr>
                  <th>It asks</th>
                  <th>Because</th>
                </tr>
              </thead>
              <tbody>
                {practice.questions.map((q) => (
                  <tr key={q.asks}>
                    <td className="ocl-table__main">{q.asks}</td>
                    <td>{q.because}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">
            {practice.lessons.length} rules, each earned by being wrong
          </h2>
          <p className="ocl-page__note">{practice.lessons_note}</p>
          <ol className="ocl-practice__lessons">
            {practice.lessons.map((lesson, i) => (
              <Lesson key={lesson.rule} lesson={lesson} n={i + 1} />
            ))}
          </ol>
        </section>

        <section className="ocl-page__section">
          <h2 className="ocl-page__sectionTitle">What it cannot do</h2>
          {practice.limits.map((item) => (
            <Item key={item.name} item={item} />
          ))}
        </section>

        <p className="ocl-page__foot">
          Kept in <code>data/practice.yml</code>. Every line traces to a file in the
          repository — the harness and its dry-runs, the drift checker and its lessons
          list, and the entries behind them in the{" "}
          <Link to="/notebook/edit-slice/ledger">evidence ledger</Link>.
        </p>
      </main>
    </Layout>
  );
}
