We are starting **Version 5 — Retrieval-Augmented Generation**, as
scoped in `docs/roadmap.md`. Versions 0–4 (foundation through the
baseline generative agent, with recorded evaluation numbers) are done
— review existing code before proceeding, and pull up the Version 4
baseline validity/uniqueness/novelty/diversity numbers, since this
version needs to compare against them. Re-read the "Retrieval-
Augmented Generation, for a Diffusion Model" section in
`docs/architecture.md` closely — this is the technical core of the
whole product.

## Goal

Condition the Version 4 diffusion model on retrieved known compounds,
implementing the RetMol-style mechanism described in
`docs/architecture.md`.

## Scope for this version only

- Project retrieved molecule embeddings (from the Version 1 embedding
  abstraction layer) into the diffusion model's conditioning space
- Inject them during the denoising process — via cross-attention if
  the Version 4 backbone architecture supports it, or via a guidance-
  vector approach if a lighter-touch integration is more tractable.
  State which approach you used and why.
- Wire this into the actual product flow: a project's retrieval
  results (Version 2) now feed directly into its generation requests
  (Version 4), rather than generation running in isolation
- Implement the fallback path from `docs/architecture.md`: when
  retrieval returns weak/no relevant matches, fall back to the
  Version 4 plain property-conditioned generation, and surface that
  fallback explicitly in the API response (don't silently degrade)
- Re-run the Version 4 evaluation suite on retrieval-conditioned
  generations and compare directly against the Version 4 baseline:
  does conditioning measurably shift generated candidates closer to
  the retrieved set (e.g. average similarity to retrieved compounds)
  without collapsing diversity? Report both sets of numbers side by
  side.

## Ground rules

- No docking yet — Version 6.
- No LangGraph orchestration yet — Version 7; for now, wiring
  retrieval into generation directly is fine.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me a real example: a project with a seed molecule,
  its retrieval results, and a generation run that visibly used those
  results as conditioning — plus the before/after evaluation
  comparison.
- Summarize what was built and be honest about the comparison
  results, including if conditioning's effect was weaker or noisier
  than expected — that's useful information for the project, not a
  failure to hide.
