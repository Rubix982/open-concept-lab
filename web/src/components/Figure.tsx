import type { ReactNode } from "react";
import clsx from "clsx";
import useBaseUrl from "@docusaurus/useBaseUrl";

export type FigureProps = {
  /** Image path. Omit and pass children instead for inline SVG or a diagram. */
  src?: string;
  /** Describe the image for people who can't see it. Falls back to caption. */
  alt?: string;
  /** Caption text; the figure number is prepended automatically. */
  caption?: ReactNode;
  /** Let the figure exceed the text measure — for wide diagrams and plots. */
  wide?: boolean;
  /** Drop the frame; for diagrams that carry their own background. */
  plain?: boolean;
  /** Tint the frame so a light UI screenshot doesn't bleed into the page. */
  screenshot?: boolean;
  children?: ReactNode;
};

/**
 * A numbered figure. Numbering comes from a CSS counter on the article body,
 * so figures renumber themselves when you reorder them.
 */
export default function Figure({
  src,
  alt,
  caption,
  wide = false,
  plain = false,
  screenshot = false,
  children,
}: FigureProps): ReactNode {
  const captionText =
    typeof caption === "string" ? caption : undefined;

  /* The site is served under a base path, and a raw <img src="/img/…"> does not
     pick it up — the request falls through to the SPA handler, which answers
     200 with HTML, so the browser shows a broken image and the build reports
     nothing. useBaseUrl leaves absolute URLs alone. */
  const resolved = useBaseUrl(src ?? "");

  return (
    <figure
      className={clsx("ocl-figure", {
        "ocl-figure--wide": wide,
        "ocl-figure--plain": plain,
        "ocl-figure--screenshot": screenshot,
      })}
    >
      <div className="ocl-figure__frame">
        {src ? <img src={resolved} alt={alt ?? captionText ?? ""} /> : children}
      </div>
      {caption ? (
        <figcaption className="ocl-figure__caption">{caption}</figcaption>
      ) : null}
    </figure>
  );
}
