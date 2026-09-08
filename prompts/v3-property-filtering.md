We are starting **Version 3 — Property Filtering Pipeline**, as
scoped in `docs/roadmap.md`. Versions 0–2 (foundation, knowledge base,
project intake/retrieval) are done — review existing code before
proceeding. Re-read the "Property Filtering" section in
`docs/architecture.md`.

## Goal

Build the RDKit-based property filtering pipeline now, while it's
cheap and low-risk, and prove its value immediately by applying it to
the retrieval results that already exist — before any generative
complexity is layered on top.

## Scope for this version only

- Implement, per molecule: QED, SA score, Lipinski's Rule of Five
  (molecular weight, logP, H-bond donors/acceptors — show each
  component, not just pass/fail), and PAINS filtering
- Apply this pipeline to the Version 2 retrieval results as the first
  real use case
- Store every filter's raw value and pass/fail per molecule — never
  collapse this into a single opaque score
- Frontend: a property breakdown per compound, plus a sortable/
  filterable comparison table (this table's structure will be reused
  for generated candidates from Version 4 onward, so design it
  generically rather than retrieval-specific)

## Ground rules

- No generation yet — Version 4. This version's filtering pipeline
  should be built generically enough to apply to generated candidates
  later without rework, but there's nothing generated to filter yet.
- No docking yet — Version 6.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me the comparison table populated with real
  retrieval results from Version 2, sorted and filtered by at least
  two different properties.
- Summarize what was built and confirm the table/filter design is
  generic enough to reuse for generated candidates.
