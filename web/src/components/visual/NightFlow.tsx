import type { ReactNode } from "react";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";
import Flow, { type FlowStep } from "@site/src/components/visual/Flow";

/**
 * One night of the harness, step by step. The step lines paraphrase the
 * harness entry in src/data/agentic.ts; the wake-ups are the escalation list
 * from data/practice.yml, placed at the step that raises each.
 */
export default function NightFlow(): ReactNode {
  const { practice } = usePluginData("ocl-lab-data") as LabData;
  const esc = practice?.boundary.escalation ?? [];
  const wake = (word: string) =>
    esc.filter((e) => e.trigger.includes(word)).map((e) => e.trigger);
  const steps: FlowStep[] = [
    { art: "flow-queue", title: "Queue", text: "Only pre-registered work, with its expected verdict written down first." },
    { art: "flow-preflight", title: "Preflight", text: "Gates that refuse before anything touches the network.", wakes: wake("preflight") },
    { art: "flow-run", title: "Run", text: "Each job under a budget it may not outlive.", wakes: [...wake("expect"), ...wake("budget")] },
    { art: "flow-triage", title: "Triage", text: "Every failure sorted by cause, so only the undiagnosed one needs a person.", wakes: wake("unsorted") },
    { art: "flow-report", title: "Report", text: "A page readable mid-run, with a section on what it did not check." },
  ];
  return (
    <section className="ocl-ag__sec ocl-ag__night">
      <h2>How a night runs</h2>
      <p className="ocl-page__note">
        Everything else is logged and the queue carries on. A known failure
        needs a count; an unknown one needs a person.
      </p>
      <Flow steps={steps} label="The harness's pipeline: queue, preflight, run, triage, report" />
    </section>
  );
}
