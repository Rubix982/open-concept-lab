import type { ReactNode } from "react";

/**
 * A turn from Claude in a piece written back and forth. The author's prose is
 * the page; this is a reply set into it — the apparatus face, a rule in link
 * blue, and a label — so whose words are whose is never in question.
 *
 *   <Claude re="a more precise question">
 *   The precision you want may be in the scenario, not the question.
 *   </Claude>
 */
export default function Claude({
  children,
  re,
}: {
  children?: ReactNode;
  /** The phrase of the author's this answers, quoted in the label. */
  re?: string;
}): ReactNode {
  return (
    <aside className="ocl-voice ocl-voice--claude" aria-label="Note from Claude">
      <p className="ocl-voice__who">
        <span className="ocl-voice__mark" aria-hidden="true" />
        Claude
        {re ? <span className="ocl-voice__re">on “{re}”</span> : null}
      </p>
      <div className="ocl-voice__body">{children}</div>
    </aside>
  );
}
