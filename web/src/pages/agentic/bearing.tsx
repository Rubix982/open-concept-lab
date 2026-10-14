import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";

const CHECKS: [string, string][] = [
  ["What have you never varied?",
   "Every narrowing in the research record came from unfixing a dimension that had been held constant. So the question that has actually produced results is answerable by counting."],
  ["Instrument, or the world?",
   "A run of work that only measures your own measure is how a project stops being able to say what it is for."],
  ["Does the write-up cite work that is not finished?",
   "A section of the paper asserted a claim the record had withdrawn, and did so for nine days."],
  ["Is the summary still about this project?",
   "An abstract drifts from its findings silently; nothing fails when it does."],
  ["Are sections named after claims, or after runs?",
   "A write-up organised by experiment makes the reader assemble the argument — and so does anyone asked to summarise it."],
  ["What did you price and then not do?",
   "The honestly-costed item is the one that gets postponed."],
  ["Have you stopped finding yourself wrong — or stopped checking?",
   "Both look identical from inside the project."],
  ["Does the write-up assert something about ALL of someone else's work without having checked one?",
   "A week of work was priced on such a claim. Checking it took twenty minutes and returned 0.09%."],
];

export default function Bearing(): ReactNode {
  return (
    <Layout title="bearing" description="Where a research project is pointed, measured from its own record.">
      <div className="ocl-page">
        <header className="ocl-page__head">
          <p className="ocl-page__kicker"><Link to="/agentic">Agentic</Link></p>
          <h1 className="ocl-page__title">bearing</h1>
          <p className="ocl-page__lede">
            A bearing is a measured direction, not a destination. It tells a project
            where it is pointed. It does not claim to know where it should go.
          </p>
        </header>

        <section className="ocl-ag__sec">
          <h2>Why it exists</h2>
          <p>
            Research drifts before anyone notices. After a week in which every finished
            item was a finer measurement of the project's own instrument, its author
            said: <em>“I feel we have dug ourselves too deep into narrow cases, but are
            not able to explain the high level of our research outcomes.”</em>
          </p>
          <p>
            That is a navigational correction, and it arrived from a person reading a
            trajectory. Most of what made it possible is mechanical — a property of the
            sequence, computable from the record. <code>bearing</code> asks those
            questions on a schedule so the correction arrives a week or two earlier, and
            from the record rather than from a mood.
          </p>
        </section>

        <section className="ocl-ag__sec">
          <h2>What it asks</h2>
          <p>
            Each question is phrased so that the <strong>bad answer is the computable
            one</strong>. A check that cannot come back bad is a horoscope.
          </p>
          <dl className="ocl-ag__dl">
            {CHECKS.map(([q, why]) => (
              <div key={q} className="ocl-ag__dlRow">
                <dt>{q}</dt>
                <dd>{why}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="ocl-ag__sec">
          <h2>How a check gets in</h2>
          <p>
            Backwards from an outcome, never forwards from a hunch. The rule is derived
            from something that happened, encoded, then tested against the historical
            case it came from — and only then trusted.
          </p>
          <ol className="ocl-ag__steps">
            <li><strong>The outcome.</strong> A week of work was priced on “every propagation benchmark probes with prompts that begin with the subject”, asserted having inspected none. Counting took twenty minutes and returned 0.09%.</li>
            <li><strong>The rule.</strong> A claim quantified over a class of other people's work, with no instance inspected, is the cheapest thing to check and the most expensive to be wrong about.</li>
            <li><strong>The check.</strong> A universal quantifier, plus a noun naming external work, plus nothing in the record claiming to have measured it.</li>
            <li><strong>The test.</strong> It must fire on the original text and go quiet once the measurement exists. Both are regressions.</li>
            <li><strong>It was wrong once.</strong> It fired on the paragraph that <em>withdrew</em> the claim, because that paragraph quotes it. A checker that cannot tell an assertion from its retraction punishes the behaviour it exists to encourage.</li>
          </ol>
        </section>

        <section className="ocl-ag__sec">
          <h2>Leaving it running</h2>
          <p>
            It can be left watching several projects and checked once or twice a day,
            which only works because it is <strong>differential</strong>. A watcher that
            reprints its full state every pass teaches you to skim it, and a skimmed
            watcher is off.
          </p>
          <ul className="ocl-ag__plain">
            <li><code>NEW</code> — was fine, now uncomfortable. The only alarm.</li>
            <li><code>GONE</code> — was uncomfortable, now fine.</li>
            <li><code>9d</code> — uncomfortable for nine days, unchanged. <em>Either not important, or being avoided</em> — and both are worth saying out loud, so it carries its age and leaves the distinction to you.</li>
          </ul>
          <p>
            A quiet sweep still leaves a mark. Without one, a gap in the digest is
            ambiguous between <em>nothing happened</em> and <em>the watcher was dead</em>,
            and those need opposite responses.
          </p>
        </section>

        <section className="ocl-ag__sec ocl-ag__limit">
          <h2>It has no taste</h2>
          <p>
            It measures drift, not direction. It answers whether the work has narrowed —
            never whether it matters. It answers what has never been varied — never what
            should be varied next. <strong>A project can pass every question and still be
            pointed somewhere that does not matter.</strong>
          </p>
          <p>
            Three of its checks were written with confidence and cried wolf on first
            contact. One counted a findings entry as unfinished work; one flagged the
            section whose job is listing open questions; one read a second project's
            correction ledger — a document that is entirely corrections — as evidence
            nobody was checking. <strong>A check written in one project's dialect will
            libel every project that speaks another.</strong>
          </p>
          <p>
            So it keeps a track record of what each check has actually caught, and names
            the ones that never help. A check with no catch after several firings is
            overhead — the falsification clause, made mechanical so it gets checked rather
            than quietly accreted.
          </p>
          <pre className="ocl-ag__sample">{`$ python -m bearing ai/edit-slice --track

  check                       caught  false+  verdict
  named_after_runs                 0       1  too early to say
  still_checking                   0       1  too early to say
  summary_staleness                1       0  earns its place
  unchecked_universal              1       0  earns its place
  premise_under_priced_work        1       0  earns its place`}</pre>
          <p>
            <strong>The worst failure so far was not a false alarm — it was a check that
            punished the fix it existed to ask for.</strong> One check asks whether a
            write-up's sections are named after claims or after the runs that produced
            them. A heading reading <em>“What the edit <strong>does</strong> to the rest of
            the subject”</em> was rewritten to <em>“An edit <strong>displaces</strong>
            probes whose answer type <strong>matches</strong> the injected value”</em> —
            strictly more claim-shaped — and the score got <em>worse</em>. Its verb list
            held auxiliaries only, and <code>does</code> was on it while
            <code> displaces</code> was not.
          </p>
          <p>
            A sibling check was wrong about <em>when</em> four separate times, and three of
            the four returned a plausible date rather than an error: a pickaxe that fired
            only on the commit creating a heading and never on edits to the text beneath
            it; a line-range built with Python's regex escaping where git wants POSIX; a
            date comparison with day granularity, so a summary rewritten in the morning
            read as stale by the afternoon; and a path that broke wherever a symlink sat
            between the repo root and the file — which silently fell back to the first bug
            and so survived the two fixes in between.
          </p>
          <p>
            Only the last was caught by a test, and only because that test builds a real
            repository with a known history instead of asserting on a string.
            <strong> A check that returns a plausible wrong answer is worse than one that
            crashes</strong>, and nothing but an external fact distinguishes them.
          </p>
        </section>

        <p className="ocl-page__foot">
          Source in <code>projects/bearing/</code>. The practices it belongs to are on{" "}
          <Link to="/agentic/practice">Practice</Link>.
        </p>
      </div>
    </Layout>
  );
}
