import clsx from "clsx";
import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { requestView, resetView, usePaperView } from "./paperView";

/**
 * Paper and Threads as two views of one document.
 *
 * An earlier pass made these two routes and a link between them, which meant
 * leaving the page and loading another on every click. They are not two pages.
 * They are the same work seen twice -- what was found, and what was asked on
 * the way -- so switching should replace the body and nothing else.
 *
 * The state lives in `paperView.ts` and reaches the body as a `data-view`
 * attribute on the article, with CSS doing the hiding. That is a deliberate
 * choice rather than a shortcut: the paper's body is raw MDX between the header
 * and the panel, with no React ancestor either view owns, so rendering it
 * conditionally would mean swizzling the doc layout to wrap markup neither view
 * controls. A view flag on the element both views already live inside is the
 * smaller thing.
 */
export function PaperSwitch(): ReactNode {
  const { view, pending } = usePaperView();
  const host = useRef<HTMLElement | null>(null);
  const mounted = useRef(false);

  useEffect(() => {
    const article = host.current?.closest(".markdown");
    if (!(article instanceof HTMLElement)) return;

    // Mid-swap: the outgoing content is still on screen, fading.
    if (pending !== view) {
      article.classList.add("is-swapping");
      return;
    }

    article.dataset.view = view;
    if (!mounted.current) {
      mounted.current = true;
      return;
    }

    // The incoming content is in the DOM now but still at opacity 0, because
    // `is-swapping` is on. Clearing it a frame later is what makes it fade in
    // rather than appear -- clearing it in this same commit would batch the
    // display change and the opacity change into one paint, and the transition
    // would have nothing to run from.
    const frame = requestAnimationFrame(() =>
      requestAnimationFrame(() => article.classList.remove("is-swapping")),
    );
    // The header stays put, so scrolling to the top of the body is what a
    // reader means by "switch" when they are halfway down a long paper.
    article.scrollIntoView({ block: "start", behavior: "smooth" });
    return () => cancelAnimationFrame(frame);
  }, [view, pending]);

  // Leaving the page puts the next paper back on its argument.
  useEffect(() => resetView, []);

  return (
    <nav className="ocl-paperswitch" aria-label="How to read this" ref={host}>
      <button type="button" onClick={() => requestView("paper")}
              className={clsx({ "is-here": pending === "paper" })}
              aria-pressed={pending === "paper"}>Paper</button>
      <button type="button" onClick={() => requestView("plain")}
              className={clsx({ "is-here": pending === "plain" })}
              aria-pressed={pending === "plain"}>Plain</button>
      <button type="button" onClick={() => requestView("threads")}
              className={clsx({ "is-here": pending === "threads" })}
              aria-pressed={pending === "threads"}>Threads</button>
    </nav>
  );
}

/**
 * The plain view's container: the same paper said so that someone outside the
 * field can check it.
 *
 * Held to the plain-words test rather than to "shorter": the simple version has
 * to be EASIER to prove wrong than the technical one. So the numbers stay, the
 * limits stay in a section of their own, and the one control that was got wrong
 * stays too. A version that cannot be wrong would mean the content left with the
 * notation, and the fix for that is upstream of the writing.
 *
 * The label is three words. It was "PLAIN - the same paper, said so it can still
 * be checked", which argued for the tab in the place where its name goes, and
 * claimed a virtue the page spends two thousand words demonstrating. That is now
 * `self-justifying label` in research-craft's lint, with the two tests in
 * voice.md, because neither the lint nor the census could see it: both scored
 * this file clean while that sentence was in it.
 */
export function PlainPanel({ children }: { children: ReactNode }): ReactNode {
  return (
    <section className="ocl-plainpanel" aria-label="In plain words">
      <div className="ocl-plainpanel__id">In plain words</div>
      {children}
    </section>
  );
}

/**
 * The threads view's container. Lives at the foot of the paper's own file and
 * is shown only when the switch selects it.
 */
export default function ThreadsPanel({ children }: { children: ReactNode }): ReactNode {
  return (
    <section className="ocl-threadspanel" aria-label="Threads">
      <div className="ocl-threadspanel__id">THREADS — how this paper was reached</div>
      {children}
    </section>
  );
}
