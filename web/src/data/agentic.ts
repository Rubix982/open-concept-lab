// Agentic efforts: the tools that keep research moving when nobody is watching (AGENTIC,
// each with its own page at src/pages/agentic/<name>.tsx), and the files an agent reads
// before it starts (GUIDES, each in its own public repo).
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
  // The four questions every card on /agentic answers, in plain words.
  kind: string; // a two- or three-word label for what sort of thing it is
  plain: string; // what it is, in one sentence a newcomer can follow
  agent: string; // what the agent does with it — the agentic part
  forYou: string; // what it does for the person using it
  use: string; // the commands to try it, or the step to take
  useNote?: string; // a caveat on `use`, when there is one
};

export const AGENTIC: Agentic[] = [
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
    kind: "Runs overnight",
    plain: "A queue that runs my experiments overnight and leaves a report for the morning.",
    agent:
      "Runs experiments from a queue a person wrote, refuses any that fail a check before " +
      "they start, sorts every failure by cause, and writes a report you can read mid-run.",
    forYou:
      "You stop babysitting runs. In the morning there is a report, and it only woke you " +
      "for the four things that need a person.",
    use: "git clone https://github.com/Rubix982/open-concept-lab\ncd open-concept-lab/ai/edit-slice\npython tools/watch.py",
    useNote: "Built for one project and not packaged. The code is public to copy from.",
    sample: `$ python tools/watch.py

[12:29:59] 1 job(s) queued
[12:29:59] E-036: preflight
[12:30:14] E-036: running (budget 3.0h)
[12:49:34] E-036: finished in 19 min
[12:49:34] E-036: ok — verdict ['UNDIFFERENTIATED'], report written`,
  },
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
    kind: "Checks direction",
    plain: "A command-line checker that asks whether a research project is drifting off course.",
    agent:
      "Reads a project's tickets, findings and write-up on a schedule, and raises an alarm " +
      "only when one of its questions turns from a good answer to a bad one.",
    forYou:
      "It tells you the work has narrowed or the write-up has gone stale a week or two " +
      "before you would notice it yourself.",
    use: "git clone https://github.com/Rubix982/bearing\ncd bearing && pip install -e .\nbearing ~/path/to/project",
    useNote: "Reads the ticket layout from dotclaude. Another layout needs a ~30-line adapter.",
    sample: `$ bearing ai/edit-slice

4 of 10 questions have an uncomfortable answer.

!!  Do the last 5 finished items measure your instrument, or the world?
      5 of the last 5 lean inward (E-030, E-031, E-032, E-033, E-034).
      asked because: a run of inward work is how a project stops being
      able to say its point

!!  What did you price and then not do?
      about a week — rewriting the probes is the work, scoring is hours.`,
  },
];

// Files an agent reads before it starts work. They live in their own public repos, so
// these entries link out rather than to a page here. Each sample is quoted from the
// file it names.
export type Guide = {
  name: string; // the drawing is /img/art/tools/<name>.svg
  title: string;
  what: string;
  blurb: string;
  href: string;
  file: string; // repo · file the sample is quoted from
  sample: string;
  // The four questions every card on /agentic answers, in plain words.
  kind: string; // a two- or three-word label for what sort of thing it is
  plain: string; // what it is, in one sentence a newcomer can follow
  agent: string; // what the agent does with it — the agentic part
  forYou: string; // what it does for the person using it
  use: string; // the commands to try it, or the step to take
  useNote?: string; // a caveat on `use`, when there is one
};

export const GUIDES: Guide[] = [
  {
    name: "dotclaude",
    title: "dotclaude",
    what:
      "The instructions every Claude session here starts from. It opens with why the " +
      "work exists and how to tell a real step from a toy, then sets the working rules: " +
      "one card open at a time, tickets and threads for longer efforts, and when the " +
      "heavier research protocols are allowed. It also marks the exception — side builds " +
      "like this site, where the heavy rules are set down on purpose.",
    blurb:
      "The instructions every Claude session here starts from: why the work exists, " +
      "how a card is opened, and when the heavy protocols are allowed.",
    href: "https://github.com/Rubix982/dotclaude/blob/main/CLAUDE.md",
    file: "Rubix982/dotclaude · CLAUDE.md",
    kind: "Agent instructions",
    plain: "The instruction file Claude reads at the start of every session I run.",
    agent:
      "Claude reads it at the start of every session. It sets what one unit of work is, " +
      "when to stop and ask, and which rules to drop for small side projects.",
    forYou:
      "Sessions start already knowing how you work, so you don't re-explain it, and the " +
      "agent stops before anything it can't undo.",
    use: "git clone https://github.com/Rubix982/dotclaude\n# add it to your own, don't replace it:\ncat dotclaude/CLAUDE.md >> ~/.claude/CLAUDE.md",
    useNote: "It is my own setup. Read it first and keep the parts that fit you.",
    // The file's own top-level headings, in order.
    sample: `# Manifesto
# Compass — keeping the work connected
#   to real need
# The Standard
# Side Builds — the deliberate exception
# Global Rules
# Agentic Work Template
# The Card — the default, and the width
#   limit`,
  },
  {
    name: "patternbook",
    title: "patternbook",
    what:
      "A library of design knowledge taken from human-made work — IKEA assembly manuals, " +
      "appliance troubleshooting pages — filed by the problem a page has to solve, for a " +
      "coding agent to look up before it builds. An entry is trusted only after a page " +
      "built from it wins a blind pick. The IKEA entry has won twice; the troubleshooting " +
      "entry lost, because the agent already did most of it unprompted.",
    blurb:
      "Design knowledge from human-made work, filed by the problem a page solves, for an " +
      "agent to look up. An entry counts only after it wins a blind pick.",
    href: "https://github.com/Rubix982/patternbook",
    file: "Rubix982/patternbook · METHOD.md",
    kind: "Design library",
    plain: "A library of design rules learned from real printed manuals, for agents that build web pages.",
    agent:
      "Before a coding agent builds a page, it looks up the problem the page solves and " +
      "follows rules taken from how people solved it in print — IKEA manuals, appliance guides.",
    forYou:
      "Pages that don't all come out in the same cream-and-terracotta AI look. A rule is " +
      "only trusted once a page built from it wins a blind test.",
    use: "git clone https://github.com/Rubix982/patternbook\n# then tell the agent:\n# \"read patternbook/library/<problem>/ first\"",
    useNote: "Two entries so far. One won its blind tests; the other lost and says why.",
    // The default checklist in METHOD.md (C-005).
    sample: `Given no style, 7 pages on
6 subjects came out:

cream background        7/7
warm near-black text    7/7
terracotta accent       7/7
uppercase eyebrow label 6/7
pill-shaped chips       5/7`,
  },
];
