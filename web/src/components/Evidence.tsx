import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { EvidenceRecord, LabData } from "@site/plugins/lab-data";

/**
 * An evidence id that resolves.
 *
 * The ids (`E-016`, `T-075`) already appear throughout the writing as though they point
 * at something. Making them point at something is the difference between a blog and a
 * record — DESIGN.md §5.3, and the highest-value item on that list.
 *
 * Data comes from `data/evidence.yml`, which `build_ledger.py` emits from the SAME parse
 * as the ledger page, so a link and its target cannot disagree. An id with no record
 * renders visibly wrong rather than silently plain, because a dead evidence id that looks
 * alive is worse than no id at all.
 *
 *   <Evidence id="E-016" />            → E-016, linked, with the record on hover
 *   <Evidence id="E-016">the whitened run</Evidence>  → labelled
 */
export function useEvidence(id: string): EvidenceRecord | undefined {
  const all = (usePluginData("ocl-lab-data") as LabData).evidence ?? [];
  // Prefer an exact anchor match, then the first record carrying that id — decisions
  // before findings, which is the order they are emitted in.
  return all.find((r) => r.anchor === id) ?? all.find((r) => r.id === id);
}

export default function Evidence({
  id,
  children,
}: {
  id: string;
  children?: React.ReactNode;
}): React.ReactNode {
  const record = useEvidence(id);

  if (!record) {
    return (
      <span
        className="ocl-evidence ocl-evidence--missing"
        title={`No record "${id}" in data/evidence.yml — regenerate with build_ledger.py`}
      >
        {children ?? id}
      </span>
    );
  }

  const where = record.surface === "thread" ? "Thread" : record.kind;
  const tip = [
    `${record.id} · ${where}${record.date ? ` · ${record.date}` : ""}`,
    record.title,
    record.status ? `Status: ${record.status}` : "",
    record.gist,
  ]
    .filter(Boolean)
    .join("\n\n");

  return (
    <Link
      className="ocl-evidence"
      to={`/notebook/edit-slice/ledger#${record.anchor}`}
      title={tip}
      data-surface={record.surface}
    >
      {children ?? record.id}
    </Link>
  );
}
