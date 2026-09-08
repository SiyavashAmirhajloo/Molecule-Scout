We are starting **Version 7 — Multi-Agent Orchestration via
LangGraph**, as scoped in `docs/roadmap.md`. Versions 0–6 (foundation
through docking & ranking) are done — review existing code before
proceeding. Re-read the "Agents" table and "LangGraph Workflow — Core
Stages" section in `docs/architecture.md`.

## Goal

Replace the current directly-wired sequence of endpoint calls
(retrieval → filter → generate → dock) with a real LangGraph workflow
coordinated by a Coordinator agent, so the product can intelligently
re-enter the pipeline at the right stage instead of always restarting
from scratch.

## Scope for this version only

- Implement the LangGraph workflow matching the core stages diagram in
  `docs/architecture.md`, wrapping the existing Retrieval, Property,
  Generation, and Docking logic from Versions 1–6 as graph nodes
  rather than rewriting their logic
- Coordinator agent: routes these request types appropriately —
  new project, regenerate candidates (re-enter at the generation
  stage, reusing existing retrieval results), re-dock (re-enter at
  the docking stage, reusing existing generation results), and full
  re-run
- Handle background job stages (generation, docking) correctly within
  the graph — the graph should track job state and resume
  orchestration once a Celery job completes, not block on it
- Tracing: wire up Langfuse (or structured logging if Langfuse isn't
  set up yet) so a full graph path is inspectable end-to-end,
  including the async job stages

## Ground rules

- No Report Agent yet — Version 8.
- Preserve all existing functionality — every capability built in
  Versions 1–6 should keep working, just routed through the graph now.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me a trace of two real scenarios: a full new-project
  run through the entire graph, and a "regenerate candidates" request
  that correctly re-enters at the generation stage without re-running
  retrieval.
- Summarize what was built and confirm nothing from earlier versions
  regressed.
