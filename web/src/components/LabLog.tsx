import clsx from "clsx";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

/**
 * Paper and Threads as two views of one document.
 *
 * An earlier pass made these two routes and a link between them, which meant
 * leaving the page and loading another on every click. They are not two pages.
 * They are the same work seen twice -- what was found, and what was asked on
 * the way -- so switching should replace the body and nothing else.
 *
 * The state lives in a `data-view` attribute on the article, and CSS does the
 * hiding. That is a deliberate choice rather than a shortcut: the paper's body
 * is raw MDX between the header and the panel, with no React ancestor either
 * component owns, so holding this in component state would mean swizzling the
 * doc layout to install a provider around markup neither view controls. A view
 * flag on the element both views already live inside is the smaller thing.
 */
function useView(): ["paper" | "threads", (v: "paper" | "threads") => void] {
  const [view, setView] = useState<"paper" | "threads">("paper");
  const host = useRef<HTMLElement | null>(null);

  const set = useCallback((v: "paper" | "threads") => {
    setView(v);
    const article = host.current?.closest(".markdown");
    if (article instanceof HTMLElement) {
      article.dataset.view = v;
      // The header stays put, so scrolling to the top of the body is what a
      // reader means by "switch" when they are halfway down a long paper.
      article.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }, []);

  useEffect(() => {
    const el = document.querySelector(".ocl-paperswitch");
    host.current = el instanceof HTMLElement ? el : null;
    const article = host.current?.closest(".markdown");
    if (article instanceof HTMLElement && !article.dataset.view) {
      article.dataset.view = "paper";
    }
  }, []);

  return [view, set];
}

export function PaperSwitch(): ReactNode {
  const [view, set] = useView();
  return (
    <nav className="ocl-paperswitch" aria-label="Paper or threads">
      <button type="button" onClick={() => set("paper")}
              className={clsx({ "is-here": view === "paper" })}
              aria-pressed={view === "paper"}>Paper</button>
      <button type="button" onClick={() => set("threads")}
              className={clsx({ "is-here": view === "threads" })}
              aria-pressed={view === "threads"}>Threads</button>
    </nav>
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
