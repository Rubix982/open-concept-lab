import { usePluginData } from "@docusaurus/useGlobalData";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import type { LabData } from "@site/plugins/lab-data";
import type { ReactNode } from "react";

/**
 * How much of a project's record is closed, at the head of the contents rail.
 *
 * Counts only, and deliberately: a bar labelled "40% complete" is a judgement
 * about work nobody measured, and it would be the one number on this site that
 * could not be checked. These three can be — the Threads view beside them lists
 * every card and thread they count, so a reader who doubts the figure can go
 * and count it.
 *
 * Generated into `data/record.yml` by `ai/tools/build_threads_page.py` from the
 * project's own files, so it cannot drift from them without the build failing.
 */
function Row({ label, done, total }: { label: string; done: number; total: number }): ReactNode {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <div className="ocl-record__row">
      <div className="ocl-record__line">
        <span className="ocl-record__label">{label}</span>
        <span className="ocl-record__count">
          {done}<span className="ocl-record__of"> / {total}</span>
        </span>
      </div>
      <div className="ocl-record__bar" role="img"
           aria-label={`${done} of ${total} ${label.toLowerCase()} closed`}>
        <span style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function RecordPanel(): ReactNode {
  const { metadata, frontMatter } = useDoc();
  const entry = (frontMatter as Record<string, unknown>).paper as
    | { version?: string; updated?: string }
    | undefined;
  if (!entry) return null;

  const project = metadata.id.split("/")[0];
  const data = usePluginData("ocl-lab-data") as LabData;
  const rec = data.record?.[project];
  if (!rec) return null;

  return (
    <aside className="ocl-record" aria-label="State of the record">
      <div className="ocl-record__head">
        The record
        {entry.version ? <span className="ocl-record__ver">{entry.version}</span> : null}
      </div>
      <Row label="Questions" done={rec.cards_closed} total={rec.cards} />
      <Row label="Threads" done={rec.threads_answered} total={rec.threads} />
      <Row label="Tickets" done={rec.tickets_closed} total={rec.tickets} />
      <p className="ocl-record__note">
        Counted from the project's own files. Every item is listed under{" "}
        <b>Threads</b> above, so the figure can be checked rather than believed.
      </p>
    </aside>
  );
}
