We are starting **Version 4 — Baseline Generative Agent**, as scoped
in `docs/roadmap.md`. Versions 0–3 (foundation, knowledge base,
retrieval, property filtering) are done — review existing code before
proceeding. Re-read the "Generative Model Layer (Diffusion)" section
in `docs/tech-stack.md`.

## Goal

Get a diffusion model actually generating valid molecules end-to-end
— unconditioned or simply property-conditioned, no retrieval
conditioning yet. This is the version that proves the generative core
works before Version 5 adds the novel retrieval-augmented mechanism on
top of it.

## Scope for this version only

- Pick ONE diffusion backbone per `docs/tech-stack.md` — an
  equivariant 3D model (EDM-style) or a 2D molecular graph model
  (DiGress-style). Document which you chose and why (compute budget,
  implementation maturity, fit with the conditioning approach planned
  for Version 5). Do not attempt to build both.
- Train or fine-tune it on QM9 or a filtered, size-capped ZINC subset
  — pick whichever fits the compute budget available and say so
  explicitly
- Wire generation as a Celery background job with status polling (the
  frontend should show queued/running/done/failed, not block on the
  request)
- Support simple property-conditioned generation (target ranges for
  molecular weight, logP) — no retrieval conditioning yet
- Run the Version 3 filtering pipeline against a batch of generated
  candidates, since it was built generically for this
- Compute and report the standard evaluation metrics from
  `docs/architecture.md`: validity, uniqueness, novelty, and internal
  diversity (Tanimoto distance) on a generated batch — using MOSES
  and/or GuacaMol if that's the fastest path, or reimplementing the
  metric definitions directly if not

## Ground rules

- No retrieval conditioning yet — Version 5 depends on this version's
  working baseline to compare against; don't skip ahead.
- No docking yet — Version 6.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me: a real background generation job running to
  completion, a batch of generated candidates passed through the
  Version 3 filters, and the validity/uniqueness/novelty/diversity
  numbers for that batch.
- Summarize what was built, which backbone and training data you
  chose, and the baseline evaluation numbers — Version 5 will need
  these as a comparison point.
