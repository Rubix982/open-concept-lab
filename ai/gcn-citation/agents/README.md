# Agentic Work Template

---

## Directory Structure

```
project-root/
├── plan.md                  ← orchestrator's source of truth
├── shared/
│   ├── findings.md          ← researcher writes here; all agents read
│   ├── decisions.md         ← architectural/design decisions; engineer writes
│   └── glossary.md          ← shared definitions, acronyms, domain terms
├── agents/
│   ├── orchestrator/
│   │   └── tickets.md
│   ├── researcher/
│   │   ├── tickets.md
│   │   └── findings/        ← raw research, papers, notes (internal only)
│   ├── engineer/
│   │   ├── tickets.md
│   │   └── workspace/       ← scratch code, spikes, implementation notes
│   └── documentor/
│       ├── tickets.md
│       └── drafts/          ← docs, READMEs, changelogs in progress
```

**Rules:**

- `agents/shared/` is read by all agents, written only by the agent that owns it
- Raw agent output stays inside `agents/<role>/` — never in `agents/shared/`
- `plan.md` is owned by the orchestrator; no other agent writes to it

---

## Ticket ID Scheme

Global, unique, never reused.

| Prefix | Agent        |
| ------ | ------------ |
| `O-`   | Orchestrator |
| `R-`   | Researcher   |
| `E-`   | Engineer     |
| `D-`   | Documentor   |

Format: `<PREFIX><zero-padded number>` — e.g. `E-007`, `R-012`, `O-001`

IDs increment monotonically. Closed tickets keep their ID. Never reassign.

---

## Ticket Format

```markdown
### E-007 · Implement ONNX embedding microservice

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Build a Python FastAPI microservice that accepts text input and returns
ONNX-generated embeddings. Must be containerized and expose a /embed endpoint.

**Blockers:**

- R-004 (researcher must finalize model choice before implementation begins)

**RCA:** _(fill only when a ticket is re-opened after a failure)_

> What broke, why it broke, what was misunderstood. One paragraph max.

**Artifacts:**

- engineer/workspace/embed_service/
- agents/shared/decisions.md → "Embedding Model Selection"

**Closed:** —
```

---

## Ticket Status Lifecycle

```
open → in-progress → [blocked] → in-progress → closed
                                              ↘ re-opened (attach RCA)
```

- **open** — identified, not started
- **in-progress** — actively being worked
- **blocked** — waiting on another ticket or external input; blockers field must be filled
- **closed** — done; artifacts recorded
- **re-opened** — was closed, found incomplete or broken; RCA required before resuming

---

## Ticket Types

| Type         | Meaning                                                                       |
| ------------ | ----------------------------------------------------------------------------- |
| `research`   | Investigate, read, synthesize — output goes to `agents/shared/findings.md`           |
| `implement`  | Write or modify code — output stays in `engineer/workspace/`                  |
| `coordinate` | Orchestrator only — open/close/sequence tickets across agents                 |
| `review`     | Evaluate prior output; may result in re-open + RCA                            |
| `document`   | Write user-facing or internal docs                                            |
| `spike`      | Time-boxed exploration with uncertain outcome; always time-box in description |

---

## Shared Surface Conventions

### `agents/shared/findings.md`

Owned by: **Researcher**
Format:

```markdown
## [R-003] Finding: NSF Award Data Schema

_Date: 2026-04-05_

One paragraph summary of what was found.
Key facts, links, or data points as a short list.
Confidence: high / medium / low
```

### `agents/shared/decisions.md`

Owned by: **Engineer**
Format:

```markdown
## [E-007] Decision: Embedding Model Selection

_Date: 2026-04-05_

**Decision:** Use all-MiniLM-L6-v2 via ONNX runtime.
**Rationale:** Fastest inference at acceptable quality for semantic search.
**Alternatives rejected:** OpenAI ada-002 (cost), BGE-large (too slow for batch).
**Revisit if:** Retrieval quality drops below threshold in eval.
```

### `agents/shared/glossary.md`

Owned by: **all agents** (append-only, no edits to prior entries)

```markdown
- **NDIF**: National Deep Inference Fabric — Bau Lab's inference infrastructure
- **NSF Ranker**: Saif's portfolio project for RA outreach
```

---

## `plan.md` (Orchestrator's Root Document)

```markdown
# Project: <name>

_Last updated: 2026-04-05 by O-001_

## Objective

One sentence. What does done look like?

## Current Phase

Phase 1 — Research & Scoping

## Active Tickets

| ID    | Agent      | Title                   | Status      |
| ----- | ---------- | ----------------------- | ----------- |
| R-003 | Researcher | NSF Award Schema        | in-progress |
| E-005 | Engineer   | Scraper worker skeleton | open        |

## Blocked

| ID    | Blocked By |
| ----- | ---------- |
| E-007 | R-004      |

## Completed This Session

- R-001 · Survey of NSF award API endpoints
- O-001 · Initialize project structure

## Next Orchestrator Action

Open E-005 once R-003 closes.
```

---

## Resume Prompt (paste at session start)

```
You are the <ROLE> agent for project: <PROJECT NAME>.

Your workspace: agents/<role>/
Your tickets: agents/<role>/tickets.md
Shared surface (read-only for you): agents/shared/

Your role:
<one line description of what this agent does and does not do>

Open your tickets.md. Find the highest-priority in-progress ticket.
If none, find the highest-priority open ticket and begin.
If blocked, state the blocker and do nothing until it resolves.

Do not touch agents/shared/ unless your role owns it.
Do not open tickets outside your prefix.
Report what you completed and what you're opening next.
```

---

## RCA Format (when re-opening a closed ticket)

```markdown
**RCA (Re-open: 2026-04-05):**

> E-006 was marked closed but the /embed endpoint returned incorrect dimensions
> for batch inputs > 32. Root cause: ONNX session was initialized without
> dynamic axes. Fix: re-initialize with dynamic_axes on input. Ticket re-opened.
```

RCA is one paragraph. It answers: what broke, why, what was wrong in the original understanding.

---

## `CHANGELOG.md` (Root-level, Orchestrator appends)

One entry per closed ticket, per session. Written by the orchestrator at session end — never mid-session.

```markdown
# Changelog

## 2026-04-05 · Session 3

- [R-003] Finalized NSF award data schema — findings in agents/shared/findings.md
- [E-005] Scraper worker skeleton complete — code in engineer/workspace/scraper/
- [O-002] Opened E-007, unblocked after R-003 close

## 2026-04-03 · Session 2

- [R-001] Surveyed NSF award API endpoints
- [R-002] Identified rate limit constraints on public API
- [E-004] Re-opened (see RCA on ticket) — embedding dimension bug
```

**Rules:**

- Append only. Never edit prior sessions.
- One line per closed ticket: `[ID] Title — where the artifact lives`
- Orchestrator coordination tickets (`O-`) are logged with what they opened or unblocked.
- If a session closes zero tickets, log it anyway: `## 2026-04-06 · Session 4 — no tickets closed (blocked on R-004)`

---

## Advanced Concepts

### 1. Agent Disagreement — `agents/shared/disputes.md`

When an agent reads the shared surface and disagrees with a prior conclusion, it does not silently proceed on its own assumption. It appends to `agents/shared/disputes.md`.

Owned by: **any agent** (append-only)

```markdown
## [E-007] Dispute: Embedding Model Selection

_Raised by: Engineer · Date: 2026-04-05_
_Disputes: R-003 finding in agents/shared/findings.md_

**Disagreement:**
R-003 recommends all-MiniLM-L6-v2, but batch inference at our scale will exceed
latency budget. Proposing BGE-small-en instead.

**Proceeding as:** BGE-small-en (spike in E-008)
**Resolution needed by:** before E-009 opens
**Resolved:** — (orchestrator fills this when resolved)
```

The orchestrator reviews open disputes before sequencing new tickets. Unresolved disputes block dependent work.

---

### 2. Confidence-Gated Sequencing

Every finding in `agents/shared/findings.md` carries a confidence level. The orchestrator enforces these rules when opening dependent tickets:

| Confidence | Orchestrator action                                                                     |
| ---------- | --------------------------------------------------------------------------------------- |
| `high`     | Dependent tickets open normally                                                         |
| `medium`   | Dependent implement tickets become spikes first                                         |
| `low`      | No implement tickets open; researcher must do a follow-up R- ticket to raise confidence |

This makes confidence actionable, not decorative.

---

### 3. Time-Boxing as a Ticket Primitive

Every ticket may carry two optional fields:

```markdown
**Estimated:** 2h
**Spent:** 5h
```

If `Spent` exceeds `Estimated` by 2x or more and the ticket is not closed, the agent must not continue. It must either:

- Split the ticket (see below), or
- Re-scope the description and update the estimate with a note

This is not productivity tracking. It is scope detection. A ticket 3x over estimate was misunderstood, not slow.

---

### 4. Ticket Splitting

When a ticket grows beyond its original scope mid-execution, it is not closed as complete. It is closed as `split`.

**Status addition:** `split`

```markdown
**Status:** split
**Split into:** E-011, E-012, E-013
**Reason:** Implementation revealed three distinct subsystems; original scope
was underspecified.
```

Child tickets are opened normally with their own IDs. The parent ticket is never re-opened — it exists only as a record of the split decision. The changelog logs it as:

```markdown
- [E-007] Split into E-011, E-012, E-013 — scope underestimated at open
```

---

### 5. Cross-Project Memory — `~/.agent-memory/`

A lightweight directory that lives outside any single project. The orchestrator reads from it at project initialization and appends to it when a project closes or a significant reusable decision is made.

```
~/.agent-memory/
├── infrastructure/
│   ├── embedding-service.md
│   ├── docker-multistage.md
│   └── scraper-architecture.md
├── research/
│   └── nsf-api-constraints.md
└── index.md                  ← one-line summary per entry, for fast scanning
```

Entry format:

```markdown
## Embedding Service Design

_From: NSF Ranker · Date: 2026-04-05_

FastAPI + ONNX runtime. Dynamic axes required for batch inputs.
Port to Go attempted and abandoned — ONNX Go bindings immature as of 2026-04.
Use Python microservice, containerized, expose /embed endpoint.

**Reuse condition:** Any project needing local embedding inference.
```

The orchestrator's resume prompt should include: _"Check ~/.agent-memory/index.md for prior decisions relevant to this project before opening research tickets."_ This prevents re-researching solved problems across projects.

---

## Discipline Rules

1. Never mark a ticket closed without recording its artifacts.
2. Never open a ticket without a description — "figure it out" is not a description.
3. Blockers must reference a real ticket ID, not a vague concept.
4. Shared surface entries are append-only. Old entries are never edited.
5. An agent that touches another agent's workspace has broken the model.
6. RCA is required on every re-open. No exceptions.
