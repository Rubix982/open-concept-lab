import type { ReactNode } from "react";

/**
 * A margin note. Sits in the right margin on wide screens and folds into the
 * column below 1400px, so it never competes with the main argument.
 */
export default function Aside({
  children,
}: {
  children: ReactNode;
}): ReactNode {
  return <aside className="ocl-aside">{children}</aside>;
}
