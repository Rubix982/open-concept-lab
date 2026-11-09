/**
 * A side note — DESIGN.md §5.1.
 *
 * The apparatus in this writing (evidence ids, sample sizes, caveats about how a number
 * was obtained) is interleaved with the argument, so following the prose means walking
 * through it. Moving it beside the line it belongs to is the separation §1 calls the
 * whole design problem.
 *
 * No superscript, no reference marker: the note sits next to its line and that is the
 * entire mechanism. Below 1100px it falls inline immediately after the paragraph that
 * anchors it, still in the apparatus face and still subordinate — a margin note that
 * reads as body text has failed (§4.2).
 *
 *   <Margin>Refit on 1400 keys, evaluated on 665 held out.</Margin>
 */
export default function Margin({
  children,
}: {
  children?: React.ReactNode;
}): React.ReactNode {
  /*
   * A span, not an aside, and the reason is the HTML parser rather than taste.
   * These notes are written mid-paragraph, where they belong — the note sits
   * next to its line and that is the entire mechanism. An <aside> inside a <p>
   * is invalid, so the parser closes the paragraph before it and the sentence
   * breaks in half. Floated into the gutter that was invisible; inline it is
   * not. A span styled `display: block` is valid there and renders the same.
   */
  return (
    <span className="ocl-margin" role="note">
      {children}
    </span>
  );
}
