import type { ReactNode } from "react";
import useBaseUrl from "@docusaurus/useBaseUrl";

export type FlowStep = {
  /** A drawing under static/img/art/steps/, without the extension. */
  art: string;
  title: string;
  /** One line under the title. May carry inline HTML from a data file. */
  text: string;
  /** Marks a step where a person can be woken, with the reason. HTML allowed. */
  wakes?: string[];
};

function StepArt({ name }: { name: string }): ReactNode {
  const src = useBaseUrl(`/img/art/steps/${name}.svg`);
  return <img className="ocl-flow__art" src={src} alt="" loading="lazy" decoding="async" />;
}

/**
 * A process as a row of drawn steps joined by a line a pulse travels along.
 * `loop` closes the line back to the start, for a cycle rather than a pipeline.
 */
export default function Flow({
  steps,
  loop = false,
  label,
}: {
  steps: FlowStep[];
  loop?: boolean;
  label: string;
}): ReactNode {
  return (
    <figure className={`ocl-flow${loop ? " ocl-flow--loop" : ""}`} aria-label={label}>
      <ol className="ocl-flow__steps" style={{ ["--steps" as string]: steps.length }}>
        {steps.map((step, i) => (
          <li key={step.title} className="ocl-flow__step" style={{ ["--i" as string]: i }}>
            <span className="ocl-flow__badge">
              <StepArt name={step.art} />
              <span className="ocl-flow__n">{i + 1}</span>
            </span>
            <span className="ocl-flow__title">{step.title}</span>
            <span className="ocl-flow__text" dangerouslySetInnerHTML={{ __html: step.text }} />
            {step.wakes?.map((w) => (
              <span key={w} className="ocl-flow__wake">
                <span aria-hidden="true">↑</span>
                <span dangerouslySetInnerHTML={{ __html: w }} />
              </span>
            ))}
          </li>
        ))}
      </ol>
      {loop ? (
        <figcaption className="ocl-flow__again">
          <span aria-hidden="true">↺</span> and again, on the next lab
        </figcaption>
      ) : null}
    </figure>
  );
}
