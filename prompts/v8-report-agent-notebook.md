We are starting **Version 8 — Report Agent & Research Notebook**, as
scoped in `docs/roadmap.md`. Versions 0–7 (foundation through LangGraph
orchestration) are done — review existing code before proceeding.
Re-read the "Responsible Use & Dual-Use Safety Design" section in
`docs/architecture.md` — the human-in-the-loop framing requirement
there applies directly to this version's Report Agent output.

## Goal

Turn ranked candidates into something a human researcher would
actually want to read, and give the product memory across sessions.

## Scope for this version only

- Report Agent: an LLM call (via the provider-agnostic LLM abstraction
  layer) that writes a plain-English rationale per candidate — what
  it's structurally/functionally similar to (from its retrieval
  conditioning), why it scored well, and what remains uncertain
- **Required framing**: every generated rationale must explicitly note
  that the result requires human/wet-lab verification and is a triage
  aid, not a final answer — this isn't optional copy, it's a
  requirement from `docs/architecture.md`'s responsible-use design;
  build it into the prompt template, not as a UI disclaimer bolted on
  separately
- Add the Report Agent as a new node in the Version 7 LangGraph
  workflow
- Shortlist/save functionality: let the user star candidates within a
  project
- Export: SDF file for structures, PDF for the full assembled report
  (candidates, scores, rationale)
- Memory Agent: persist project history across sessions — past
  targets, past candidate sets, saved shortlists — so returning to a
  project shows what was done before, not a blank slate

## Ground rules

- No Vision Agent yet — Version 9.
- No production hardening/safety screening agent yet — Version 10.
  This version's responsible framing is about the report's language
  and structure, not the enforced structural safety screening that
  comes later.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me a real generated report for a project's top
  candidates, an export in both SDF and PDF form, and a demonstration
  that returning to an existing project shows its prior history.
- Summarize what was built.
