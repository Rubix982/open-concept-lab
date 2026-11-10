import type { ReactNode } from "react";

export type ProjectProps = { blurb?: string; status?: string };

/**
 * A project's row in the notebook rail: its name, then what stage it is at and
 * what it is, on a second line.
 *
 * The stage used to sit at the right edge in monospace, with the name pushed
 * left by `space-between`. That read as a table rather than a list — the eye
 * went to a column of statuses at the margin instead of down the names, and
 * three of the five said the same word. Set inline ahead of the blurb it is
 * still there to read, in one left-aligned reading order, and the names get the
 * rail's left edge to themselves.
 *
 * Docusaurus takes a sidebar label as a string and renders whatever it is
 * given, so both the category and link wrappers hand it this node instead.
 */
export function projectLabel(
  label: ReactNode,
  { blurb, status }: ProjectProps,
): ReactNode {
  return (
    <span className="ocl-proj">
      <span className="ocl-proj__name">{label}</span>
      {status || blurb ? (
        <span className="ocl-proj__meta">
          {status ? <span className="ocl-proj__stage">{status}</span> : null}
          {status && blurb ? <span className="ocl-proj__sep"> · </span> : null}
          {blurb}
        </span>
      ) : null}
    </span>
  );
}
