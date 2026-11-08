---
title: "Is the flagged code still executed? Vulnerability severity that knows whether the code runs"
kind: make
status: spark
why: "Over the last couple of months I've been pinged about vulnerabilities in code that no longer runs, is never called, or is years old, and an AI scanner still rated them critical. A critical finding that nobody runs costs the same triage time as a real one."
references:
  - group: "How much of the noise is unreachable"
    title: "VulTracer slides (NDSS 2026)"
    url: "https://www.ndss-symposium.org/wp-content/uploads/F1902-zhang-slides.pdf"
    note: "Seven projects with full test coverage as dynamic ground truth. About 68% of package-level alerts were false positives, and only about 32% of flagged packages reached the vulnerable function. Slides only, so I haven't read the full paper."
  - group: "How much of the noise is unreachable"
    title: "Does the Vulnerability Threaten Our Projects? Automated Vulnerable API Detection for Third-Party Libraries"
    url: "https://arxiv.org/pdf/2409.02753"
    note: "Checks whether a project actually calls the vulnerable API of a library it depends on."
  - group: "How much of the noise is unreachable"
    title: "Overrated and underperforming: transitive reachability analysis (Semgrep)"
    url: "https://semgrep.dev/blog/2024/overrated-and-underperforming-transitive-reachability-analysis"
    note: "A vendor's argument that call-graph reachability says 'reachable' when the real conditions for the bug are never met. Vendor view, not a study."
  - group: "Saying 'not affected' in a standard way"
    title: "CISA, VEX Status Justifications"
    url: "https://www.cisa.gov/sites/default/files/2023-01/VEX_Status_Justification_Jun22.pdf"
    note: "Defines vulnerable_code_not_in_execute_path. It warns that an attacker may be able to divert execution, so a path must not be assumed unreachable. That is the counter-argument to this whole idea, and the reason it needs evidence."
  - group: "Saying 'not affected' in a standard way"
    title: "Docker Scout, creating VEX statements"
    url: "https://docs.docker.com/scout/guides/vex/"
    note: "vexctl writing not_affected with that justification for a package inside an image."
---

**The itch.** A finding gets its severity from the code. Whether that code is still called, still deployed, or dead for years is a different question, and right now a person answers it after the alert has already cost them time. A scanner, or a model, that rates a finding critical without asking that question can be very good at reading code and still be wrong about my system.

**What I'd want to know first.** Before building anything:

- Of the alerts I actually got, how many were on code that never runs? I should count my own before trusting anyone's percentage.
- Does any scanner or model today lower a finding's severity because the code is unreachable, and how often is that lowering wrong?

**The hard part.** "Never runs" is a claim, and CISA's own guidance warns against assuming it. Static call graphs miss reflection and dynamic dispatch, and runtime coverage only shows what happened to run during the window it watched. So the useful output isn't "not affected". It's "not affected, and here is the evidence", meaning a call graph, runtime coverage over some period, or a deploy record showing the module isn't shipped. A reader can check that evidence and disagree with it.

**Where it sits.** It sits next to [what AI agents can prove](/someday/what-ai-agents-can-prove): that idea asks whether a finding is real, and this one asks whether a real finding matters here.

Not fleshed out yet. This is a spark.
