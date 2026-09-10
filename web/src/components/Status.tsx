import type { ReactNode } from "react";

export type StatusKind =
  | "draft"
  | "provisional"
  | "standing"
  | "superseded"
  | "closed";

const LABELS: Record<StatusKind, string> = {
  draft: "Draft — actively being written",
  provisional: "Provisional — may turn out to be wrong",
  standing: "Standing — survived review so far",
  superseded: "Superseded — kept for the record",
  closed: "Closed",
};

/** An inline status mark. Oxide red means "not settled". */
export function Status({
  kind,
  children,
}: {
  kind: StatusKind;
  children?: ReactNode;
}): ReactNode {
  return (
    <span className={`ocl-status ocl-status--${kind}`}>
      {children ?? LABELS[kind]}
    </span>
  );
}

/** The banner form, for the top of a page that isn't finished. */
export function Notice({ children }: { children: ReactNode }): ReactNode {
  return <div className="ocl-notice">{children}</div>;
}

export default Status;
