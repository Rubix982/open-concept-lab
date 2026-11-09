import useBrokenLinks from "@docusaurus/useBrokenLinks";
import type { ReactNode } from "react";

/**
 * A link target that Docusaurus knows about.
 *
 * A plain `<span id="...">` written into MDX produces a working anchor in the built
 * HTML and a *broken anchor* in the build log, which is the worst of both: the link
 * works, so nobody investigates, and the warning never clears, so a genuinely broken
 * anchor hides among the false ones.
 *
 * The reason is that Docusaurus does not scan the rendered HTML for ids. It collects
 * anchors only from components that register one — its own `Link` and `Details`, and
 * the MDX heading component — through `useBrokenLinks().collectAnchor`. Raw HTML is
 * invisible to it. So this component registers the id and then renders the same span.
 *
 * Use it wherever a link target is not a heading.
 */
export default function Anchor({ id }: { id: string }): ReactNode {
  useBrokenLinks().collectAnchor(id);
  return <span id={id} />;
}

/**
 * Register a list of link targets that are rendered as ordinary elements.
 *
 * `<Anchor>` suits MDX, where the target is written by hand. A page component that
 * builds its own sections — one per topic, one per track — already puts the id on the
 * `<section>`, and wrapping each in a span to satisfy the checker would add an element
 * for the sake of a warning. This registers the same ids instead.
 *
 * `collectAnchor` is a plain function off the hook's return value, not a hook itself,
 * so calling it once per id is fine however the list is shaped.
 */
export function useAnchors(ids: readonly string[]): void {
  const brokenLinks = useBrokenLinks();
  ids.forEach((id) => brokenLinks.collectAnchor(id));
}
