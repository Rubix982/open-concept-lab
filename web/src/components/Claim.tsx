import type { ReactNode } from "react";

export type ClaimProps = {
  /** Label above the rule. Defaults to "Current claim". */
  label?: string;
  /** The earlier, wider claim. Rendered struck through. */
  superseded?: ReactNode;
  /** What the claim narrowed to. Rendered as the standing statement. */
  children: ReactNode;
  /** Labelled rows beneath: project, confidence, revised date, and so on. */
  record?: Record<string, ReactNode>;
};

/**
 * A claim, shown mid-revision: what was given up, and what still stands.
 * This is the site's one deliberately loud element — use it sparingly.
 */
export default function Claim({
  label = "Current claim",
  superseded,
  children,
  record,
}: ClaimProps): ReactNode {
  return (
    <div className="ocl-claim">
      <span className="ocl-claim__label">{label}</span>
      {/* Divs, not paragraphs: in MDX the children arrive already wrapped in
          a <p>, and a nested <p> is invalid and breaks hydration. */}
      {superseded ? (
        <div className="ocl-claim__superseded">{superseded}</div>
      ) : null}
      <div className="ocl-claim__standing">{children}</div>
      {record ? (
        <dl className="ocl-claim__record">
          {Object.entries(record).map(([term, value]) => (
            <div key={term} style={{ display: "contents" }}>
              <dt>{term}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}
