import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import { AGENTIC, type Agentic } from "@site/src/data/agentic";
import PageArt from "@site/src/components/PageArt";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";
import Boundary from "@site/src/components/visual/Boundary";
import Flow, { type FlowStep } from "@site/src/components/visual/Flow";

/** A tool's drawing, with its real output laid over it in a terminal window. */
function Shot({ art, sample, file }: { art: string; sample: string; file: string }): ReactNode {
  const src = useBaseUrl(`/img/art/tools/${art}.svg`);
  return (
    <div className="ocl-ag__entryShot ocl-ag__shot">
      <img className="ocl-ag__shotArt" src={src} alt="" loading="lazy" decoding="async" />
      <div className="ocl-ag__window">
        <p className="ocl-ag__windowBar" aria-hidden="true">
          <span /><span /><span />
          <code>{file}</code>
        </p>
        <pre className="ocl-ag__sample">{sample}</pre>
      </div>
    </div>
  );
}

/**
 * One night of the harness, step by step. The step lines paraphrase the
 * harness entry in src/data/agentic.ts; the wake-ups are the escalation list
 * from data/practice.yml, placed at the step that raises each.
 */
function NightFlow(): ReactNode {
  const { practice } = usePluginData("ocl-lab-data") as LabData;
  const esc = practice?.boundary.escalation ?? [];
  const wake = (word: string) =>
    esc.filter((e) => e.trigger.includes(word)).map((e) => e.trigger);
  const steps: FlowStep[] = [
    { art: "flow-queue", title: "Queue", text: "Only pre-registered work, with its expected verdict written down first." },
    { art: "flow-preflight", title: "Preflight", text: "Gates that refuse before anything touches the network.", wakes: wake("preflight") },
    { art: "flow-run", title: "Run", text: "Each job under a budget it may not outlive.", wakes: [...wake("expect"), ...wake("budget")] },
    { art: "flow-triage", title: "Triage", text: "Every failure sorted by cause, so only the undiagnosed one needs a person.", wakes: wake("unsorted") },
    { art: "flow-report", title: "Report", text: "A page readable mid-run, with a section on what it did not check." },
  ];
  return (
    <section className="ocl-page__section ocl-ag__night">
      <h2 className="ocl-page__sectionTitle">How a night runs</h2>
      <p className="ocl-page__note">
        Everything else is logged and the queue carries on. A known failure
        needs a count; an unknown one needs a person.
      </p>
      <Flow steps={steps} label="The harness's pipeline: queue, preflight, run, triage, report" />
    </section>
  );
}

function Entry({ item }: { item: Agentic }): ReactNode {
  const page = `/agentic/${item.name}`;
  return (
    <article className="ocl-ag__entry">
      <Shot art={item.name} sample={item.sample} file={item.where} />
      <div className="ocl-ag__entryBody">
        <h2 className="ocl-ag__entryTitle">
          <Link to={page}>{item.title}</Link>
        </h2>
        <p className="ocl-ag__entryWhat">{item.what}</p>
        <p className="ocl-ag__entryMeta">
          <code>{item.where}</code> · since {item.since}
        </p>
        <p className="ocl-ag__actions">
          <Link to={page} className="ocl-ag__primary">Read about it</Link>
        </p>
      </div>
    </article>
  );
}

export default function AgenticIndex(): ReactNode {
  return (
    <Layout
      title="Agentic"
      description="Tools that keep research moving when nobody is watching, and the boundary they are built around."
    >
      <div className="ocl-page">
        <header className="ocl-page__head ocl-page__head--art">
          <PageArt name="agentic" />
          <h1 className="ocl-page__title">Agentic</h1>
          <p className="ocl-page__lede">
            Research stops when attention does. These are the tools that keep it
            moving in the hours nobody is at the desk — and, more importantly, the
            line they are built not to cross. They run the work, gate it, sort its
            failures and report it. They do not choose what to run next, decide
            whether a result is real, or write a word of the record.
          </p>
          <p className="ocl-page__lede">
            Every rule below was earned by being wrong. Each one carries the
            incident that produced it, because a rule without its failure is a
            slogan. The practices are collected on{" "}
            <Link to="/agentic/practice">Practice</Link>; the research they serve
            is in the <Link to="/notebook/edit-slice/">notebook</Link>.
          </p>
        </header>
        <Boundary />
        <NightFlow />
        <h2 className="ocl-page__sectionTitle ocl-ag__toolsTitle">The tools, the practice, and the instructions</h2>
        {AGENTIC.map((item) => (
          <Entry key={item.name} item={item} />
        ))}
        <article className="ocl-ag__entry">
          <Shot art="practice" file="agentic/practice" sample={`A green harness is not a
sound experiment.

E-036 passed every gate and
still measured two of six
criteria in ways that could
not answer their own
questions.`} />
          <div className="ocl-ag__entryBody">
            <h2 className="ocl-ag__entryTitle">
              <Link to="/agentic/practice">The practice, and its limits</Link>
            </h2>
            <p className="ocl-ag__entryWhat">
              The boundary between what a loop may own and what a person must;
              the twelve rules two projects learned by being wrong, each with its
              incident and what it cost; and an honest account of what none of it
              can catch.
            </p>
            <p className="ocl-ag__actions">
              <Link to="/agentic/practice" className="ocl-ag__primary">Read it</Link>
            </p>
          </div>
        </article>
        {/* The sample is the file's own top-level headings, in order. */}
        <article className="ocl-ag__entry">
          <Shot art="dotclaude" file="Rubix982/dotclaude · CLAUDE.md" sample={`# Manifesto
# Compass — keeping the work connected
#   to real need
# The Standard
# Side Builds — the deliberate exception
# Global Rules
# Agentic Work Template
# The Card — the default, and the width
#   limit`} />
          <div className="ocl-ag__entryBody">
            <h2 className="ocl-ag__entryTitle">
              <a href="https://github.com/Rubix982/dotclaude/blob/main/CLAUDE.md" target="_blank" rel="noreferrer">
                dotclaude
              </a>
            </h2>
            <p className="ocl-ag__entryWhat">
              The instructions every Claude session here starts from. It opens
              with why the work exists and how to tell a real step from a toy,
              then sets the working rules: one card open at a time, tickets and
              threads for longer efforts, and when the heavier research protocols
              are allowed. It also marks the exception — side builds like this
              site, where the heavy rules are set down on purpose.
            </p>
            <p className="ocl-ag__entryMeta">
              <code>Rubix982/dotclaude</code> · public on GitHub
            </p>
            <p className="ocl-ag__actions">
              <a
                href="https://github.com/Rubix982/dotclaude/blob/main/CLAUDE.md"
                target="_blank"
                rel="noreferrer"
                className="ocl-ag__primary"
              >
                Read it on GitHub ↗
              </a>
            </p>
          </div>
        </article>
      </div>
    </Layout>
  );
}
