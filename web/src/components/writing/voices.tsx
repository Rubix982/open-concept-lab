import { createContext, useContext, type ReactNode } from "react";

type Voices = { mineOnly: boolean; setMineOnly: (value: boolean) => void };

/** Whether Claude's notes are showing in the post being read. */
export const VoicesContext = createContext<Voices>({
  mineOnly: false,
  setMineOnly: () => {},
});

/**
 * Read both halves of the conversation, or only the author's. Hiding the notes
 * is the honest test of a piece written with an AI: the author's prose should
 * still stand on its own.
 */
export function VoicesToggle({
  notes,
  author,
}: {
  notes: number;
  author: string;
}): ReactNode {
  const { mineOnly, setMineOnly } = useContext(VoicesContext);
  return (
    <div className="ocl-voices" role="group" aria-label="Voices shown">
      <span className="ocl-voices__legend">
        <span className="ocl-voices__swatch ocl-voices__swatch--author" aria-hidden="true" />
        {author}
        <span className="ocl-voices__swatch ocl-voices__swatch--claude" aria-hidden="true" />
        Claude · {notes} {notes === 1 ? "note" : "notes"}
      </span>
      <span className="ocl-voices__switch">
        <button type="button" aria-pressed={!mineOnly} onClick={() => setMineOnly(false)}>
          Both
        </button>
        <button type="button" aria-pressed={mineOnly} onClick={() => setMineOnly(true)}>
          {author} only
        </button>
      </span>
    </div>
  );
}
