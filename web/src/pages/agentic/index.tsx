import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import { AGENTIC, type Agentic } from "@site/src/data/agentic";

function Entry({ item }: { item: Agentic }): ReactNode {
  const page = `/agentic/${item.name}`;
  return (
    <article className="ocl-ag__entry">
      <div className="ocl-ag__entryShot">
        <pre className="ocl-ag__sample">{item.sample}</pre>
      </div>
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
        <header className="ocl-page__head">
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
        {AGENTIC.map((item) => (
          <Entry key={item.name} item={item} />
        ))}
        <article className="ocl-ag__entry">
          <div className="ocl-ag__entryShot">
            <pre className="ocl-ag__sample">{`A green harness is not a
sound experiment.

E-036 passed every gate and
still measured two of six
criteria in ways that could
not answer their own
questions.`}</pre>
          </div>
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
      </div>
    </Layout>
  );
}
