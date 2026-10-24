import type { ReactNode } from "react";
import useBaseUrl from "@docusaurus/useBaseUrl";

/**
 * The drawing at the head of a tab — what the page is, said as a picture.
 * Drawings live in static/img/art/ and are made by scripts/draw-art.py, so
 * they share one hand.
 *
 *   <PageArt name="notebook" />
 */
export default function PageArt({
  name,
  kind = "tabs",
}: {
  name: string;
  /** "tabs" for a page's header, "projects" for a project's card. */
  kind?: "tabs" | "projects";
}): ReactNode {
  const src = useBaseUrl(`/img/art/${kind}/${name}.svg`);
  return (
    <figure className={`ocl-art ocl-art--${kind}`} aria-hidden="true">
      <img src={src} alt="" loading={kind === "tabs" ? "eager" : "lazy"} decoding="async" />
    </figure>
  );
}
