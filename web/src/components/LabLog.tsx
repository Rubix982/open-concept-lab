import useBaseUrl from "@docusaurus/useBaseUrl";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import clsx from "clsx";
import type { ReactNode } from "react";

/**
 * The switch between a paper and the log of how it was reached.
 *
 * `ai/CLAUDE.md` forbids process vocabulary -- card, thread, ticket, run --
 * from entering an argument, because it describes how work was organised and
 * not what it found. That leaves the history homeless: a reader cannot see
 * which questions were opened, in what order, or which came back the other
 * way. This gives it a page of its own beside the paper, reachable in one
 * click and ignorable in none.
 *
 * Rendered on both pages so the pair reads as one object with two faces.
 */
export function PaperSwitch({ here }: { here: "paper" | "log" }): ReactNode {
  const { metadata } = useDoc();
  const project = metadata.id.split("/")[0];
  const paper = useBaseUrl(`/notebook/${project}/paper`);
  const log = useBaseUrl(`/notebook/${project}/lab-log`);
  return (
    <nav className="ocl-paperswitch" aria-label="Paper or lab log">
      <a href={paper} className={clsx({ "is-here": here === "paper" })}
         aria-current={here === "paper" ? "page" : undefined}>Paper</a>
      <a href={log} className={clsx({ "is-here": here === "log" })}
         aria-current={here === "log" ? "page" : undefined}>Lab log</a>
    </nav>
  );
}

/**
 * The lab log's own header.
 *
 * Deliberately NOT `<Paper>`: paper mode is selected by `.ocl-paperhead` being
 * a direct child of `.markdown`, and a log read in two justified columns is a
 * worse log. It takes the switch and a plain title instead.
 */
export default function LabLogHead({ of }: { of: string }): ReactNode {
  return (
    <header className="ocl-loghead">
      <PaperSwitch here="log" />
      <div className="ocl-loghead__id">LAB LOG · {of}</div>
      <h1 className="ocl-loghead__title">How this paper was reached</h1>
    </header>
  );
}
