import { Fragment, type ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import PageArt from "@site/src/components/PageArt";
import { AS_OF, GRAPHICS, REUSE, type GraphicsCard } from "@site/src/data/graphics";

// Same card as /agentic, so the two sections read alike. The questions on each card
// come from the card's own data, since a reference library and a design library for
// agents don't answer the same two questions.

function Card({ card }: { card: GraphicsCard }): ReactNode {
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
        <p className="ocl-agc__what">{card.plain}</p>
        <dl className="ocl-agc__qa">
          {card.qa.map(([q, a]) => (
            <Fragment key={q}>
              <dt>{q}</dt>
              <dd>{a}</dd>
            </Fragment>
          ))}
        </dl>
        <div className="ocl-agc__try">
          <p className="ocl-agc__tryLabel">Try it</p>
          <pre>{card.use}</pre>
          {card.useNote && <p className="ocl-agc__note">{card.useNote}</p>}
        </div>
        <p className="ocl-agc__more">
          <Link {...link}>{card.external ? "On GitHub ↗" : "What it has found →"}</Link>
        </p>
      </div>
    </article>
  );
}

export default function GraphicsIndex(): ReactNode {
  return (
    <Layout
      title="Graphics"
      description="Two libraries for graphics work: reuse techniques in the computation behind images, and design knowledge for the pages they sit on."
    >
      <div className="ocl-page">
        <header className="ocl-page__head ocl-page__head--art">
          <PageArt name="graphics" />
          <h1 className="ocl-page__title">Graphics</h1>
          <p className="ocl-page__lede">
            Graphics in two senses: the computation that makes images, and the design
            of the pages they sit on. Two libraries so far. Each collects what people
            have already worked out, and each counts an entry only once it has been
            checked against what an AI agent would have done without it.
          </p>
          <dl className="ocl-tally">
            <div>
              <dt>Libraries</dt>
              <dd>{GRAPHICS.length}</dd>
            </div>
            <div>
              <dt>Reuse entries</dt>
              <dd>{REUSE.entries}</dd>
            </div>
            <div>
              <dt>Measured</dt>
              <dd>{REUSE.measured}</dd>
            </div>
            <div>
              <dt>Papers read in full</dt>
              <dd>{REUSE.readInFull}</dd>
            </div>
          </dl>
        </header>

        <div className="ocl-agc__grid">
          {GRAPHICS.map((c) => (
            <Card key={c.name} card={c} />
          ))}
        </div>

        <section className="ocl-agc__rule" aria-labelledby="gfx-connect">
          <h2 id="gfx-connect" className="ocl-agc__ruleTitle">How the two connect</h2>
          <p className="ocl-page__note">
            graphics-reuse takes its method from patternbook: start from the problem,
            go to the primary source, write down when the advice stops applying, and
            check what an agent already does before writing anything. They differ in how
            an entry is tested. patternbook puts a page built from the entry in front of
            a judge in a blind pick. graphics-reuse measures the reused result against a
            fresh full computation. More on <Link to="/graphics/reuse">graphics-reuse</Link>{" "}
            and on <Link to="/agentic">Agentic</Link>, where patternbook also appears.
          </p>
          <p className="ocl-page__note">Figures as of {AS_OF}.</p>
        </section>
      </div>
    </Layout>
  );
}
