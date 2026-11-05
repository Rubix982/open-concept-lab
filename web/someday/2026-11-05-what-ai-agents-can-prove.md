---
title: "A map of which vulnerabilities AI agents can actually prove, and which they can't"
kind: make
status: exploring
why: "AI security tools now promise verified findings and zero false positives. Nobody says which kinds of bugs that promise covers, so people can't see the tools' real strengths or their blind spots."
references:
  # Agents that write and check exploits: the method the map is about
  - group: "Papers: agents that write and check exploits"
    title: "PoCGen: Generating Proof-of-Concept Exploits for Vulnerabilities in npm Packages"
    url: "https://arxiv.org/html/2506.04962v3"
    note: "LLM plus static and dynamic analysis, refining until an exploit validates. Roughly 70–77% on SecBench.js depending on paper version, about $0.02 per exploit."
  - group: "Papers: agents that write and check exploits"
    title: "PoC-Gym: Towards More Reliable LLM-Assisted Proof-of-Concept Exploit Generation"
    url: "https://arxiv.org/html/2602.04165v3"
    note: "Java, 20 CVEs. LLM exploits often look valid at runtime but aren't, so deeper trace checks are needed. The cheating problem, measured."
  - group: "Papers: agents that write and check exploits"
    title: "FaultLine: Automated Proof-of-Vulnerability Generation Using LLM Agents"
    url: "https://arxiv.org/abs/2507.15241"
    note: "Proof-of-vulnerability tests for Java, reasoning about data flow and branch conditions in a feedback loop."
  - group: "Papers: agents that write and check exploits"
    title: "PAGENT: Program Analysis Guided LLM Agent for Proof-of-Concept Generation"
    url: "https://arxiv.org/html/2604.07624"
    note: "Static analysis writes the report, the agent writes the exploit, dynamic checks feed back."
  - group: "Papers: agents that write and check exploits"
    title: "AnyPoC: Universal Proof-of-Concept Test Generation for Scalable LLM-Based Bug Detection"
    url: "https://arxiv.org/pdf/2604.11950"
    note: "Proof-of-concept tests as the filter on LLM bug detection. Not yet read in detail."
  - group: "Papers: agents that write and check exploits"
    title: "SAST-Genius: A Hybrid Static Analysis Framework"
    url: "https://arxiv.org/pdf/2509.15433"
    note: "Fine-tuned LLM triage on a commercial scanner: false alarms 225 → 20, valid exploits for about 70% of confirmed findings."
  - group: "Papers: agents that write and check exploits"
    title: "PoCEvolve: Generating Proof-of-Concept Exploits from Security Patches"
    url: "https://arxiv.org/pdf/2607.22076"
    note: "Starts from the patch and works back to an exploit. Not yet read."
  - group: "Papers: agents that write and check exploits"
    title: "FirmAgent: Leveraging Fuzzing to Assist LLM Agents with IoT Firmware (NDSS 2026)"
    url: "https://netsec.ccert.edu.cn/files/papers/ndss26-firmagent.pdf"
    note: "Fuzzing confirms whether static-analysis alerts on firmware are exploitable."
  - group: "Papers: agents that write and check exploits"
    title: "Prompt to Pwn: Automated Exploit Generation for Smart Contracts"
    url: "https://arxiv.org/pdf/2508.01371"
    note: "Frontier models produced only a handful of valid exploits and missed multi-contract attack chains."

  # Benchmarks, and the few results broken down by bug class
  - group: "Papers: benchmarks and per-class evidence"
    title: "CVE-Bench: AI Agents' Ability to Exploit Real-World Web Application Vulnerabilities (ICML 2025)"
    url: "https://proceedings.mlr.press/v267/zhu25i.html"
    note: "40 critical web CVEs in sandboxes, eight standard attack types, automatic grading. Best agent about 13%."
  - group: "Papers: benchmarks and per-class evidence"
    title: "CVE-Factory: Scaling Expert-Level Agentic Tasks for Code Security Vulnerability"
    url: "https://arxiv.org/pdf/2602.03012"
    note: "Per-class rates, but for repair: access control 27.1%, command injection 46.6%, code injection 10.8%. The complication in the hypothesis."
  - group: "Papers: benchmarks and per-class evidence"
    title: "Autonomous LLM Agents & CTFs: A Second Look"
    url: "https://arxiv.org/html/2605.21497v1"
    note: "Agents consistently miss business-logic flaws and default to hunting injections. Case studies, not rates."
  - group: "Papers: benchmarks and per-class evidence"
    title: "ZeroDayBench: Evaluating LLM Agents on Unseen Zero-Day Vulnerabilities"
    url: "https://arxiv.org/html/2603.02297v1"
    note: "One setup went from 0% to 80% when the prompt named the bug class. Hint level must be recorded."
  - group: "Papers: benchmarks and per-class evidence"
    title: "ExploitBench: A Capability Ladder Benchmark for LLM Cybersecurity Agents"
    url: "https://arxiv.org/html/2605.14153v1"
    note: "A proof counts only if it fires on the vulnerable build and not the fixed one."
  - group: "Papers: benchmarks and per-class evidence"
    title: "VulnRepairEval: An Exploit-Based Evaluation Framework for LLM Vulnerability Repair"
    url: "https://pith.science/paper/2509.03331"
    note: "23 Python CVEs: a fix counts only if the exploit stops working. Best of twelve models about 21.7%."
  - group: "Papers: benchmarks and per-class evidence"
    title: "LLM Agents can Autonomously Exploit One-day Vulnerabilities"
    url: "https://arxiv.org/pdf/2404.08144"
    note: "GPT-4 drops to 7% without the CVE description."
  - group: "Papers: benchmarks and per-class evidence"
    title: "Teams of LLM Agents can Exploit Zero-Day Vulnerabilities (EACL 2026)"
    url: "https://aclanthology.org/2026.eacl-long.2.pdf"
    note: "Overall rates, no per-class breakdown."

  # The closest prior art to the map itself
  - group: "Surveys and SoKs: the closest prior art"
    title: "SoK: Measuring What Matters for Closed-Loop Security Agents"
    url: "https://arxiv.org/html/2510.01654v1"
    note: "Organised by pipeline stage (find, confirm, patch, validate), not by bug class. The nearest thing to this map."
  - group: "Surveys and SoKs: the closest prior art"
    title: "SoK: DARPA's AI Cyber Challenge (AIxCC)"
    url: "https://arxiv.org/abs/2602.07666"
    note: "Competition design and lessons. Proofs judged by sanitizers on C and Java with harnesses provided: the high-oracle, low-context corner of the map, done well."
  - group: "Surveys and SoKs: the closest prior art"
    title: "SoK: Large Language Models in Security Code Review and Testing"
    url: "https://openreview.net/forum?id=hMkoe4C44D"
    note: "Detection, fuzzing and exploit generation compared with traditional tools. Appears to be a submission."
  - group: "Surveys and SoKs: the closest prior art"
    title: "LLMs in Software Security: A Survey of Vulnerability Detection Techniques"
    url: "https://arxiv.org/html/2502.07049v2"
    note: "Memory bugs get higher detection accuracy; logic bugs are underexplored."
  - group: "Surveys and SoKs: the closest prior art"
    title: "A Systematic Literature Review on Detecting Software Vulnerabilities with LLMs"
    url: "https://arxiv.org/html/2507.22659v2"
    note: "227 studies; on why results across papers aren't comparable."
  - group: "Surveys and SoKs: the closest prior art"
    title: "Sifting the Noise: LLM Agents in Vulnerability False Positive Filtering"
    url: "https://arxiv.org/pdf/2601.22952"
    note: "Filtering false alarms without writing exploits. The cheaper alternative to proof."
  - group: "Surveys and SoKs: the closest prior art"
    title: "IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities (ICLR 2025)"
    url: "https://proceedings.iclr.cc/paper_files/paper/2025/file/582d4e27fa24168f3af1f4582655034b-Paper-Conference.pdf"
    note: "LLMs write CodeQL source and sink specs and filter taint alerts."

  # Agents with access as the attacker's shortcut through context
  - group: "Agents with access: context an attacker can borrow"
    title: "The lethal trifecta for AI agents (Simon Willison, 2025)"
    url: "https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/"
    note: "Private data, untrusted content and a way to send things out: any agent with all three can be turned against its owner."
  - group: "Agents with access: context an attacker can borrow"
    title: "AgentDojo: Evaluating Prompt Injection Attacks and Defenses for LLM Agents"
    url: "https://arxiv.org/abs/2406.13352"
    note: "A benchmark of tool-using agents hijacked through the content they read."
  - group: "Agents with access: context an attacker can borrow"
    title: "GitHub MCP exploited: accessing private repositories (Invariant Labs)"
    url: "https://invariantlabs.ai/blog/mcp-github-vulnerability"
    note: "A real case: a malicious public issue steers an agent into leaking private repos through its own credentials."
  - group: "Agents with access: context an attacker can borrow"
    title: "OWASP Top 10 for LLM Applications: Excessive Agency (LLM06:2025)"
    url: "https://genai.owasp.org/llmrisk/llm062025-excessive-agency/"
    note: "The standard name for giving an agent more permission, function or autonomy than its job needs."

  # What developers can actually run today
  - group: "AI security checks available today"
    title: "Claude Code security review (GitHub Action and /security-review)"
    url: "https://github.com/anthropics/claude-code-security-review"
    note: "Anthropic's reviewer for pull requests and the terminal. Reviews code; I found no evidence it writes exploit proofs."
  - group: "AI security checks available today"
    title: "OpenAI Codex Security (Axios coverage, March 2026)"
    url: "https://www.axios.com/2026/03/06/openai-codex-security-ai-cyber"
    note: "Tests suspected bugs in sandboxes and generates exploits to confirm them; reportedly reviews every pull request."
  - group: "AI security checks available today"
    title: "GitHub Copilot Autofix for code scanning"
    url: "https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/responsible-use-autofix-code-scanning"
    note: "Suggests fixes for CodeQL alerts. Fixes, not proofs."
  - group: "AI security checks available today"
    title: "Semgrep Assistant"
    url: "https://semgrep.dev/docs/semgrep-assistant/overview"
    note: "AI triage and fix suggestions on Semgrep findings."
  - group: "AI security checks available today"
    title: "XBOW"
    url: "https://xbow.com"
    note: "Autonomous pentesting agent that validates web findings by exploiting them; topped HackerOne's leaderboard in 2025."
  - group: "AI security checks available today"
    title: "DARPA AIxCC final results"
    url: "https://www.darpa.mil/news/2025/aixcc-results"
    note: "Autonomous systems found 86% of the planted bugs at the 2025 finals (a later SoK says 77%) and had to prove each one."
  - group: "AI security checks available today"
    title: "Buttercup, Trail of Bits' AIxCC system (2nd place, now open source)"
    url: "https://blog.trailofbits.com/2025/08/09/trail-of-bits-buttercup-wins-2nd-place-in-aixcc-challenge/"
    note: "A full find, prove and patch system anyone can run, for the easy corner of the map."
  - group: "AI security checks available today"
    title: "AIxCC finals: Tale of the tape (Trail of Bits)"
    url: "https://blog.trailofbits.com/2025/08/07/aixcc-finals-tale-of-the-tape/"
    note: "How the finals were scored: proofs, patches, SARIF alert assessment, bundles and an accuracy multiplier."

  # What I'd build the map with
  - group: "Open tooling and data for building the map"
    title: "OWASP Top 10"
    url: "https://owasp.org/Top10/"
    note: "Broken access control at #1: the class the hypothesis predicts these tools prove least."
  - group: "Open tooling and data for building the map"
    title: "CVE-Bench harness"
    url: "https://github.com/uiuc-kang-lab/cve-bench"
    note: "Sandboxed web CVEs with automatic grading, for running a class or two myself."
  - group: "Open tooling and data for building the map"
    title: "SecBench.js"
    url: "https://github.com/cristianstaicu/SecBench.js"
    note: "npm vulnerabilities with exploits, the dataset PoCGen was measured on."
  - group: "Open tooling and data for building the map"
    title: "CVEfixes"
    url: "https://github.com/secureIT-project/CVEfixes"
    note: "Real CVEs paired with their fix commits: vulnerable and fixed versions side by side."
  - group: "Open tooling and data for building the map"
    title: "OWASP Benchmark"
    url: "https://owasp.org/www-project-benchmark/"
    note: "Test programs labelled real bug or false alarm, for scanner accuracy."
  - group: "Open tooling and data for building the map"
    title: "Semgrep CE"
    url: "https://github.com/semgrep/semgrep"
    note: "Open-source scanner; free to run and publish results on."
  - group: "Open tooling and data for building the map"
    title: "CodeQL"
    url: "https://codeql.github.com/"
    note: "GitHub's query-based scanner; free for open-source code."
  - group: "Open tooling and data for building the map"
    title: "Bandit"
    url: "https://github.com/PyCQA/bandit"
    note: "Python security linter, the simplest baseline."
---

**The idea.** Read the papers that have AI agents write and run proof-of-concept exploits, pull out how well the agents did on each kind of vulnerability, and put it on one map. The map tells a developer or a buyer when to trust a "verified" finding, and where these tools are quietly silent.

**The hypothesis, stated before reading anything.** An agent can prove a bug when the bug sets off an alarm by itself, and struggles when "wrong" depends on what the business intended. Every verified exploit needs an oracle, something observable that says the attack worked, and bug classes differ a lot in whether one exists. My predictions:

- Memory bugs in C/C++: a sanitizer fires or the program crashes. Predicted high.
- ReDoS (slow regular expressions): the alarm is timing. Predicted high.
- Command injection, path traversal: a marker file gets written or read. Predicted medium to high.
- SQL injection, XSS: a marker shows up in the output or the database. Predicted medium.
- Deserialization, prototype pollution: depends on finding a gadget that does something visible. Predicted medium.
- Broken access control, IDOR, business logic: no alarm. Seeing record #42 is only wrong if this user shouldn't see it, and nothing in the code says so. Predicted low.
- Race conditions: timing-dependent and flaky. Predicted low.

**Revised the same day: context is the second axis.** The oracle is only half of it. Before an agent can show an attack worked, it has to reach the bug: get the system running, configured, logged in as the right user, holding the right data, through the right sequence of steps. A scanner throws that context away when it flags a line of code, and that is why the alerts stay noisy. It can see the pattern, but not whether the conditions to reach it ever exist in this system. So proof is hard in two separate ways: how observable success is, and how much of the system the agent has to rebuild to get there. The levels of context, from least to most:

- One function: call it with a bad input. Most library CVEs.
- A library's public API, inside a small harness.
- A running service with its real configuration.
- An authenticated, multi-step workflow: log in as a role, create some state, then attack.
- A chain across several services or systems.

The revised prediction is that proof rates fall along both axes, and that context depth matters at least as much as the oracle. Access control is the worst case on both: there is no alarm, and the question only makes sense once roles, seeded data and the intended policy exist. The existing numbers hint at this but are not comparable, because they come from different papers: PoCGen, where reaching the bug mostly means calling an npm function, is around 70%. CVE-Bench, on full deployed web apps, is about 13%, and its authors spent 5–24 person-hours per CVE just reproducing them. Rebuilding context is expensive for people too. The one-day exploit paper falling to 7% without the CVE description says the same thing, because the description is context. AIxCC is the clean case from the other side: its organisers handed every system the harness, so context depth was low by design, and that is the setting where autonomous proof worked best. I read that as support for the context axis, but it is an inference: AIxCC had no deep-context tasks to compare against.

**Why the context axis matters more every year.** Companies keep giving agents wider access: they're logged in, hold roles across services, and know which systems exist and how to call them. That is exactly the context that makes deep bugs hard to reach. An attacker who can steer such an agent, usually through prompt injection hidden in an email, ticket or web page the agent reads, inherits all of it for free, and the depth stops protecting anyone. It's the old "confused deputy" problem: a program with authority tricked into using it for someone else. Simon Willison's "lethal trifecta" puts the danger plainly: private data, untrusted content, and a way to send things out. This suggests a sharper hypothesis, still untested: the bugs AI tools are worst at proving (access control, business logic, anything deep in context) may be the ones privileged agents make easiest to exploit. If that holds, the tools' blind spot and the fastest-growing risk are the same place.

**Why it would matter.** Broken access control is the #1 category in the OWASP Top 10, and it is the one I predict these tools are worst at proving. If that holds, "zero false positives" can be true precisely because the tool says nothing about the most common serious class. No vendor will publish that, which is why an independent map is worth doing, and why doing it alone is not a handicap.

**What the prior-art search found (5 Nov 2026, one pass).** I found no survey that maps verifiability by bug class around the oracle question. The closest are [SoK: Measuring What Matters for Closed-Loop Security Agents](https://arxiv.org/html/2510.01654v1), which is organised by pipeline stage (finding, confirming, patching, validating) rather than by bug class, and [SoK: LLMs in Security Code Review and Testing](https://openreview.net/forum?id=hMkoe4C44D), which looks like a submission rather than a published paper. The closest working example is DARPA's AI Cyber Challenge (AIxCC, finals at DEF CON 2025), which does much of what this idea wants: a finding counted only with a proof of vulnerability, an input that reproduces the crash; a patch counted only if that proof stopped working and the project still ran; one task was judging whether static-analysis alerts were real; wrong submissions cut a team's score; and no human could touch a system during scored runs. But it ran entirely in one corner of the map: C and Java projects where a sanitizer gives a crisp alarm, each with a ready-made test harness, so roughly context level 2. In that corner, autonomous systems found 77–86% of the planted bugs (the [SoK on AIxCC](https://arxiv.org/abs/2602.07666) and DARPA disagree on the figure) at about $152 per successful task. AIxCC shows the method works where both axes are favourable, done well and at scale. It never tested web apps, access control, business logic or deep context, so it says nothing about the rest of the map. It is the anchor for the easy corner, not prior art for the whole. Early evidence lines up with the hypothesis, with one complication:

- [Autonomous LLM Agents & CTFs: A Second Look](https://arxiv.org/html/2605.21497v1): agents consistently miss business-logic flaws and default to searching for injections and misconfigurations. A case study, not a rate.
- [Detection survey](https://arxiv.org/html/2502.07049v2): memory bugs get higher detection accuracy, logic bugs are underexplored. That's detection, not proof.
- [CVE-Factory](https://arxiv.org/pdf/2602.03012) has per-class rates, but for *repair*, not exploitation: access control 27.1%, OS command injection 46.6%, and code injection only 10.8%. So "injection is easy" is too coarse, and code injection may behave differently from command injection. That's the complication.
- [ZeroDayBench](https://arxiv.org/html/2603.02297v1): one setup went from 0% to 80% when the prompt named the bug class. The hint level can swamp everything else, so it has to be recorded.
- [LLM Agents can Autonomously Exploit One-day Vulnerabilities](https://arxiv.org/pdf/2404.08144): GPT-4 drops to 7% without the CVE description. Same lesson.

**How to do it.**

- For each paper, record the bug class (CWE), the task (detect, exploit or repair), the oracle used to judge success, the context depth the agent had to rebuild (the five levels above), the hint level it was given, the benchmark, the model and the success rate. Note setup cost too when a paper reports it.
- Bug class and context depth travel together, because access control almost always needs a deep context. To tell the two axes apart, look for the same bug class at different depths, for example injection in a bare function against injection behind a login.
- Compare bug classes only within a paper. Never average across papers: benchmarks, models and success definitions all differ, so 70% in one paper and 13% in another mean nothing side by side.
- Note which oracle each class actually used in each paper. If the hypothesis is right, the oracle type should explain more of the variation than the model does.
- Later, fill a gap by running one or two classes myself on open-source code, for example the npm setup from [PoCGen](https://arxiv.org/html/2506.04962v3).

**What would prove it wrong.** If agents prove access-control and logic bugs about as often as injection bugs, within the same paper and at the same hint level, the hypothesis fails, and the map says so plainly. CVE-Factory's low code-injection number is already a warning that the boundary may not fall where I drew it. The context half fails if, for the same bug class at the same hint level, proof rates do not drop as context depth rises.

**First step, small enough for one sitting.** Pull the per-class numbers, task, oracle, context depth and hint level out of three papers (PoCGen, CVE-Factory, CTFs Second Look) into one sheet, and check whether either pattern shows up at all before reading any more.

**Limits and cautions.** The search was one pass. I didn't check the IEEE S&P, USENIX Security or NDSS proceedings directly, so a survey of exactly this may exist; check there first. Most of the sources are 2025–26 preprints. If I ever run commercial tools, check their terms of service before publishing anything, since many forbid publishing benchmarks. Stay with open-source tools and public CVEs.
