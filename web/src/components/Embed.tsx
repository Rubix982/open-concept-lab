import type { ReactNode } from "react";
import clsx from "clsx";
import useBaseUrl from "@docusaurus/useBaseUrl";

export type EmbedProps = {
  /**
   * Either an absolute URL (a Netlify page, say) or a site-relative path to a
   * file under `static/` — `/demos/lookback/index.html`.
   */
  src: string;
  /** Describes the embedded page for screen readers and browser tooling. */
  title: string;
  /** Caption text; shares figure numbering with <Figure>. */
  caption?: ReactNode;
  /** Fixed pixel height. Use for pages that don't scale with width. */
  height?: number;
  /** Width-to-height ratio when no height is given. Defaults to 16 / 10. */
  ratio?: number;
  /** Let the embed exceed the text measure. On by default. */
  wide?: boolean;
  /** Show the "open in a new tab" link. On by default. */
  standalone?: boolean;
  /**
   * Extra sandbox permissions. Scripts and same-origin are always allowed,
   * since these embeds are interactive pages you wrote.
   */
  allow?: string;
};

const isExternal = (src: string): boolean => /^https?:\/\//.test(src);

/**
 * Static hosts redirect a trailing `/index.html` to the directory, and an
 * iframe handling that redirect is one more thing to go wrong. Ask for the
 * directory in the first place.
 */
const normalize = (src: string): string =>
  src.replace(/\/index\.html$/, "/");

/**
 * A live interactive page, embedded. Works for a self-hosted file under
 * `static/` and for a page deployed elsewhere; the only difference is whether
 * `src` is a path or a URL.
 */
export default function Embed({
  src,
  title,
  caption,
  height,
  ratio = 16 / 10,
  wide = true,
  standalone = true,
  allow,
}: EmbedProps): ReactNode {
  const external = isExternal(src);
  // Hooks run unconditionally; useBaseUrl leaves absolute URLs alone.
  const basedSrc = useBaseUrl(normalize(src));
  const resolved = external ? src : basedSrc;

  return (
    <figure
      className={clsx("ocl-figure", "ocl-embed", {
        "ocl-figure--wide": wide,
      })}
    >
      <div
        className="ocl-embed__frame"
        style={
          height
            ? { height: `${height}px` }
            : { aspectRatio: `${ratio}` }
        }
      >
        <iframe
          className="ocl-embed__iframe"
          src={resolved}
          title={title}
          loading="lazy"
          allow={allow}
          allowFullScreen
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"
        />
      </div>
      {caption || standalone ? (
        <figcaption className="ocl-figure__caption">
          {caption ? <span className="ocl-embed__caption">{caption}</span> : null}
          {standalone ? (
            <span className="ocl-embed__note">
              <a
                className="ocl-embed__standalone"
                href={resolved}
                target="_blank"
                rel="noreferrer"
              >
                {external
                  ? "Open this on its own page (hosted separately)"
                  : "Open this on its own page"}
              </a>
            </span>
          ) : null}
        </figcaption>
      ) : null}
    </figure>
  );
}
