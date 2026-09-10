# Orchestrator Tickets — edit-slice

### O-001 · Initialize edit-slice project structure

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-09-09
**Updated:** 2026-09-09

**Description:**
Lay down the agentic workspace template (plan.md, threads.md, agents/*, and the
notes/refs/probes/src/results layout from CLAUDE.md) for a repo that contained
only CLAUDE.md and one session note. Check ~/.agent-memory/index.md for reusable
prior decisions before opening research tickets.

**Artifacts:**
- plan.md, threads.md, agents/**, refs/, probes/, src/, results/
- ~/.agent-memory checked — only entry is ats-job-board-apis.md, not relevant.

**Closed:** 2026-09-09

---

### O-002 · Resolve the edit-slice / rome-neighbors scope collision

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-09-09
**Updated:** 2026-09-09

**Description:**
User directed (2026-09-09) that backward probing be treated as a new phase of
rome-neighbors rather than a separate repo. Executing that as stated would
overwrite a scope lock made with Natalie and Arnab, so it is held pending an
explicit decision.

The collision, precisely:
- rome-neighbors/plan.md (2026-07-22) frames the project as forward ripple
  propagation, N1-N4 hops. That is the version the merge option was described
  from, and it is stale.
- rome-neighbors/threads.md (2026-08-23) locks direction to the LOOP:
  predict -> edit -> evaluate -> repair -> certify.
- rome-neighbors/design_system.md v0.2 (2026-08-24) re-forks to KEEP, a
  parametric<->retrieval consistency certifier for hybrid RAG+editing systems.
  The ripple-repair framing is archived in Appendix A as superseded.
- edit-slice/CLAUDE.md forbids proposing a method ("Not a method... proposing a
  method means owning the burden of beating JNO") and demotes the RAG framing
  ("leading with cost invites 'RAG already solves this, cheaper'").

So the two scopes contradict on both axes: method-vs-instrument, and
RAG-seam-vs-compiler-oracle. A merge is a scope decision, not a file move.

**Resolution (2026-09-10):** **Reuse code, not scope.** No conceptual merge.
edit-slice stays a separate repo and a separate claim; rome-neighbors stays
KEEP with its 2026-08-24 Fork B lock intact. edit-slice may import
rome-neighbors' plumbing so the pilot is not rebuilt from scratch. Per-module
boundary deferred to T-005.

**Blockers:** none (resolved)

**Artifacts:**
- threads.md -> T-001 answered, T-005 opened
**Closed:** 2026-09-10
