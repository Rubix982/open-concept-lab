import type { ReactNode } from "react";
import useBaseUrl from "@docusaurus/useBaseUrl";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

function Who({ name }: { name: string }): ReactNode {
  const src = useBaseUrl(`/img/art/steps/${name}.svg`);
  return <img className="ocl-bound__who" src={src} alt="" decoding="async" />;
}

/**
 * The judgement boundary, drawn: what the loop may own on one side, what only
 * a person may do on the other, and the four things that cross from one to
 * the other. Every word comes from data/practice.yml.
 */
export default function Boundary(): ReactNode {
  const { practice } = usePluginData("ocl-lab-data") as LabData;
  if (!practice) return null;
  const { rule, owns, refuses, escalation } = practice.boundary;
  const [loopPart, personPart] = rule.split(/\.\s+/);

  return (
    <section className="ocl-bound" aria-label="The judgement boundary">
      <div className="ocl-bound__side ocl-bound__side--loop">
        <Who name="who-loop" />
        <h2 className="ocl-bound__title">{loopPart.replace(/\.$/, "")}.</h2>
        <ul className="ocl-bound__list">
          {owns.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </div>

      <div className="ocl-bound__line" aria-hidden="true">
        <span className="ocl-bound__pulse" />
      </div>

      <div className="ocl-bound__side ocl-bound__side--person">
        <Who name="who-person" />
        <h2 className="ocl-bound__title">{(personPart ?? "").replace(/\.$/, "")}.</h2>
        <ul className="ocl-bound__list">
          {refuses.map((r) => (
            <li key={r}>{r[0].toUpperCase() + r.slice(1)}</li>
          ))}
        </ul>
      </div>

      <div className="ocl-bound__wakes">
        <p className="ocl-bound__wakesTitle">
          What crosses the line: the loop wakes a person on exactly {escalation.length} things
        </p>
        <ol>
          {escalation.map((e) => (
            <li key={e.trigger}>
              <span className="ocl-bound__trigger" dangerouslySetInnerHTML={{ __html: e.trigger }} />
              <span className="ocl-bound__why" dangerouslySetInnerHTML={{ __html: e.why }} />
            </li>
          ))}
        </ol>
        <p className="ocl-bound__more">
          Why the line sits here, and what it cost to learn: <Link to="/agentic/practice">Practice</Link>
        </p>
      </div>
    </section>
  );
}
