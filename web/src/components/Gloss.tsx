import { useId, useState, type ReactNode } from "react";

/**
 * Claude's note on one phrase of the author's, the way a reader writes in the
 * margin of someone else's draft. The phrase is marked in place; the note sits
 * in the gutter on wide screens, and opens under the line when the phrase is
 * tapped on narrow ones.
 *
 *   I wanted <Gloss on="a cleaner answer">Cleaner than what? The null was
 *   clean — it just wasn't the answer you were hoping for.</Gloss> and it isn't there.
 */
export default function Gloss({
  on,
  children,
}: {
  /** The author's words being glossed, as they read in the sentence. */
  on: string;
  children?: ReactNode;
}): ReactNode {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <span className={`ocl-gloss${open ? " ocl-gloss--open" : ""}`}>
      <button
        type="button"
        className="ocl-gloss__phrase"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(!open)}
      >
        {on}
      </button>
      <span className="ocl-gloss__note" id={id} role="note">
        <span className="ocl-gloss__who">Claude</span> {children}
      </span>
    </span>
  );
}
