// Agentic efforts: the tools that keep research moving when nobody is watching, and the
// judgement boundary they are built around. Each has its own page at
// src/pages/agentic/<name>.tsx.
//
// The prose on those pages is sourced from the repository — bearing now lives in
// its own repo at github.com/Rubix982/bearing (a submodule at projects/bearing/),
// `ai/edit-slice/tools/`, and the research record under `ai/edit-slice/agents/shared/`.
// Nothing here is written from memory; a claim that cannot be traced to a file is left out.

export type Agentic = {
  name: string; // the page is /agentic/<name>
  title: string;
  what: string;
  blurb: string; // one line, for the home-page card — not a truncation of `what`
  where: string; // path in this repository
  since: string;
  sample: string; // real output, pasted — not a mock
};

export const AGENTIC: Agentic[] = [
  {
    name: "bearing",
    title: "bearing",
    what:
      "A bearing is a measured direction, not a destination. It reads a project's own " +
      "record and asks the questions that correct course — what has never been varied, " +
      "whether the work has turned inward, whether the write-up still matches the " +
      "findings. It measures drift. It has no taste, and says so.",
    blurb:
      "Reads a project's own record and asks the questions that correct course. " +
      "It measures drift, and has no taste.",
    where: "github.com/Rubix982/bearing",
    since: "14 October 2026",
    sample: `$ bearing ai/edit-slice

4 of 10 questions have an uncomfortable answer.

!!  Do the last 5 finished items measure your instrument, or the world?
      5 of the last 5 lean inward (E-030, E-031, E-032, E-033, E-034).
      asked because: a run of inward work is how a project stops being
      able to say its point

!!  What did you price and then not do?
      about a week — rewriting the probes is the work, scoring is hours.`,
  },
  {
    name: "harness",
    title: "The unattended harness",
    what:
      "Four pieces that let an experiment run without anyone watching: gates that refuse " +
      "before anything touches the network, a triage that sorts every failure by cause so " +
      "only the undiagnosed one needs a person, a report page readable mid-run, and a loop " +
      "that escalates on exactly four things. It owns execution. A person owns judgement.",
    blurb:
      "Gates that refuse before anything touches the network, a triage that sorts " +
      "failures by cause, and a loop that escalates on exactly four things.",
    where: "ai/edit-slice/tools/",
    since: "14 October 2026",
    sample: `$ python tools/watch.py

[12:29:59] 1 job(s) queued
[12:29:59] E-036: preflight
[12:30:14] E-036: running (budget 3.0h)
[12:49:34] E-036: finished in 19 min
[12:49:34] E-036: ok — verdict ['UNDIFFERENTIATED'], report written`,
  },
];
