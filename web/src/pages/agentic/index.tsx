import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { AGENTIC, GUIDES } from "@site/src/data/agentic";
import Boundary from "@site/src/components/visual/Boundary";
import PageArt from "@site/src/components/PageArt";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

// The page is the cards. Each one answers the same four questions in the same
// order — what it is, what the agent does, what you get, how to try it — so a
// reader can compare them without scrolling past diagrams first. The diagrams
// live on the pages they explain (the night's flow on /agentic/harness).

type Card = {
  name: string;
  title: string;
  kind: string;
  what: string;
  agent: string;
  forYou: string;
  use: string;
  useNote?: string;
  href: string;
  external: boolean;
};

const CARDS: Card[] = [
  ...AGENTIC.map((a) => ({ ...a, what: a.plain, href: `/agentic/${a.name}`, external: false })),
  ...GUIDES.map((g) => ({ ...g, what: g.plain, external: true })),
];

function ProjectCard({ card }: { card: Card }): ReactNode {
  const art = useBaseUrl(`/img/art/tools/${card.name}.svg`);
  const link = card.external
    ? { href: card.href, target: "_blank", rel: "noreferrer" }
    : { to: card.href };
  return (
    <article className="ocl-agc">
      <Link {...link} className="ocl-agc__art" tabIndex={-1} aria-hidden="true">
        <img src={art} alt="" loading="lazy" decoding="async" />
      </Link>
      <div className="ocl-agc__body">
        <p className="ocl-agc__kind">{card.kind}</p>
        <h2 className="ocl-agc__title">
          <Link {...link}>{card.title}</Link>
        </h2>
        <p className="ocl-agc__what">{card.what}</p>
        <dl className="ocl-agc__qa">
          <dt>What the agent does</dt>
          <dd>{card.agent}</dd>
          <dt>What you get</dt>
          <dd>{card.forYou}</dd>
        </dl>
        <div className="ocl-agc__try">
          <p className="ocl-agc__tryLabel">Try it</p>
          <pre>{card.use}</pre>
          {card.useNote && <p className="ocl-agc__note">{card.useNote}</p>}
        </div>
        <p className="ocl-agc__more">
          <Link {...link}>{card.external ? "On GitHub ↗" : "How it works →"}</Link>
        </p>
      </div>
    </article>
  );
}

export default function AgenticIndex(): ReactNode {
  const { practice } = usePluginData("ocl-lab-data") as LabData;
  const unattended = AGENTIC.length;
  return (
    <Layout
      title="Agentic"
      description="Four things built for working with AI agents: what each does, and how to use it."
    >
      <div className="ocl-page">
        <header className="ocl-page__head ocl-page__head--art">
          <PageArt name="agentic" />
          <h1 className="ocl-page__title">Agentic</h1>
          <p className="ocl-page__lede">
            Four things I built for working with AI agents. Two run work while
            nobody is at the desk; two are files an agent reads before it starts.
            Each card says what it does and how to try it.
          </p>
          <dl className="ocl-tally">
            <div>
              <dt>Tools</dt>
              <dd>{CARDS.length}</dd>
            </div>
            <div>
              <dt>Run unattended</dt>
              <dd>{unattended}</dd>
            </div>
            <div>
              <dt>Read first</dt>
              <dd>{CARDS.length - unattended}</dd>
            </div>
            {practice && (
              <div>
                <dt>Reasons to wake me</dt>
                <dd>{practice.boundary.escalation.length}</dd>
              </div>
            )}
            {practice && (
              <div>
                <dt>Rules learned</dt>
                <dd>{practice.lessons.length}</dd>
              </div>
            )}
          </dl>
        </header>

        <div className="ocl-agc__grid">
          {CARDS.map((c) => (
            <ProjectCard key={c.name} card={c} />
          ))}
        </div>

        <section className="ocl-agc__rule" aria-labelledby="agc-rule">
          <h2 id="agc-rule" className="ocl-agc__ruleTitle">The line the agents don't cross</h2>
          <p className="ocl-page__note">
            The agent runs the work. It does not decide what to run next, whether a
            result is real, or what goes in the write-up. Each rule behind that line,
            and the mistake that taught it, is on{" "}
            <Link to="/agentic/practice">Practice</Link>.
          </p>
          <Boundary />
        </section>
      </div>
    </Layout>
  );
}
