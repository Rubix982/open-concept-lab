import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import NightFlow from "@site/src/components/visual/NightFlow";

const PIECES: [string, string, string][] = [
  ["preflight", "gates that refuse, not warn",
   "Lint, import, cache-key consistency, cache completeness, the run's own reporting path against known-answer data, and one real round trip — cheapest first, before anything touches the network. A gate that warns is a gate nobody reads at 3am."],
  ["triage", "every failure by cause; UNSORTED is the output",
   "Each warning matched to a known failure mode, carrying the record entry that diagnosed it, so a line at 3am points at the decision that explains it. A known failure needs a count; an unknown one needs a person."],
  ["report", "one page per run, readable mid-run",
   "Built only from what the run left on disk, so a run still going renders with its missing pieces marked. What needs a human eye goes first, then the ticket's pre-stated outcomes beside the verdict that actually fired."],
  ["watch", "the loop, and its four alarms",
   "Preflight, run, triage, report, next. It escalates on a refused gate, an unsorted failure, a verdict outside what was expected, or a job outliving its budget. Everything else is logged and the queue carries on."],
];

export default function Harness(): ReactNode {
  return (
    <Layout title="The unattended harness" description="Running experiments when nobody is watching, and the line that work stops at.">
      <div className="ocl-page">
        <header className="ocl-page__head">
          <p className="ocl-page__kicker"><Link to="/agentic">Agentic</Link></p>
          <h1 className="ocl-page__title">The unattended harness</h1>
          <p className="ocl-page__lede">
            Four pieces that let an experiment run with nobody at the desk. The loop owns
            execution. A person owns judgement. That split is the design, not a
            limitation.
          </p>
        </header>

        <section className="ocl-ag__sec">
          <h2>What it cost to not have one</h2>
          <p>
            Every piece below exists because of a specific loss, and none of those losses
            was research:
          </p>
          <div className="ocl-table__scroll">
            <table>
              <thead>
                <tr><th>what happened</th><th className="ocl-table__num">cost</th></tr>
              </thead>
              <tbody>
                <tr><td>Two jobs sat in a backend's <code>RECEIVED</code> state, never queued and never erroring. No exception was raised, so the retry logic never fired.</td><td className="ocl-table__num">144 hours</td></tr>
                <tr><td>A backoff tuned for random flakiness, against a failure that recovered on the next attempt every time.</td><td className="ocl-table__num">29% of a run, asleep</td></tr>
                <tr><td>A gate that measured lift on the injected target — a quantity a logit nudge also moves.</td><td className="ocl-table__num">2 hours, and a withdrawn headline</td></tr>
                <tr><td>A partial cache read as complete; a cache key missing a parameter that changes the number; a flaky node misread as an oversized batch.</td><td className="ocl-table__num">four re-runs</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="ocl-ag__sec">
          <h2>The pieces</h2>
          <dl className="ocl-ag__dl">
            {PIECES.map(([name, tag, body]) => (
              <div key={name} className="ocl-ag__dlRow">
                <dt><code>{name}</code> — {tag}</dt>
                <dd>{body}</dd>
              </div>
            ))}
          </dl>
        </section>

        <NightFlow />

        <section className="ocl-ag__sec">
          <h2>The boundary</h2>
          <p>
            The loop does not choose what to run next, judge whether a result is real,
            write a record entry, close a ticket, or touch the write-up. Three reasons,
            all from the project's own record rather than from principle:
          </p>
          <ul className="ocl-ag__plain">
            <li>
              A meta-analysis of the project's seventeen results found that <strong>every
              narrowing came from choosing which held-fixed dimension to vary.</strong>
              That choice is judgement, and it is the step that has reliably produced
              results. A loop picking its own next experiment would be guessing at the
              one move that works.
            </li>
            <li>
              Three separate results cost a withdrawn claim to interpreting a result too
              eagerly — twice from a headline written before a confound check had
              finished. A loop that interpreted results would reproduce that failure
              faster than anyone could catch it.
            </li>
            <li>
              The write-up already names the real risk as <em>“a large, internally
              consistent body of work that nobody outside has stress-tested.”</em>{" "}
              <strong>Automating generation without automating scrutiny makes that worse,
              not better.</strong> So every report carries a section headed <em>what this
              page did not check</em> — as a section, not a footnote.
            </li>
          </ul>
        </section>

        <section className="ocl-ag__sec ocl-ag__limit">
          <h2>What it cannot catch</h2>
          <p>
            Its first end-to-end run passed everything: preflight six of six, all four
            verdict branches exercised by the dry-run, zero unsorted failures, the verdict
            firing exactly as pre-registered, nineteen minutes, no intervention.
          </p>
          <p>
            It also measured two of its six criteria in ways that could not answer their
            own questions — and one of those was a confound the ticket had named{" "}
            <em>before</em> the run.
          </p>
          <p>
            <strong>Gates catch broken code and broken process. A construct-validity error
            passes every one of them</strong>, because the code does exactly what it was
            asked and the question was wrong. The only thing that catches it is a person
            reading the numbers and asking whether the measurement could have come out any
            other way.
          </p>
          <p>
            Write the gates anyway. Just do not mistake a green harness for a sound
            experiment.
          </p>
        </section>

        <p className="ocl-page__foot">
          Source in <code>ai/edit-slice/tools/</code>. The rules behind it are on{" "}
          <Link to="/agentic/practice">Practice</Link>.
        </p>
      </div>
    </Layout>
  );
}
