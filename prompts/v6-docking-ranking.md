We are starting **Version 6 — Docking & Composite Ranking**, as
scoped in `docs/roadmap.md`. Versions 0–5 (foundation through
retrieval-augmented generation) are done — review existing code before
proceeding. Re-read the "Docking & Composite Ranking" section in
`docs/architecture.md` and the "Docking" section in
`docs/tech-stack.md`.

## Goal

Turn generated, filtered candidates into ranked, actionable results by
docking them against the project's target protein.

## Scope for this version only

- Receptor/ligand preparation using Open Babel/MGLTools (PDB → PDBQT
  conversion, adding hydrogens, assigning charges) — this needs real
  target protein structures now, not just the PDB ID reference stored
  since Version 2, so fetch/prepare the actual structure file
- AutoDock Vina integration, run as a Celery background job (docking
  is slow — do not run it inline)
- Compute the composite rank score from `docs/architecture.md`
  (docking affinity + drug-likeness + novelty), and disclose the exact
  formula and formula version in both the API response and the
  frontend — never show a rank score without it
- Frontend: 3D docking pose viewer (3Dmol.js or NGL per
  `docs/tech-stack.md`) and a ranked candidate table
- If feasible within scope, sanity-check the docking setup against a
  benchmark target with known actives/decoys (e.g. a DUD-E target) —
  known actives should score better than decoys. If this doesn't fit
  cleanly into this version's scope, flag it as a follow-up rather
  than skipping validation of the docking setup entirely.

## Ground rules

- No LangGraph orchestration yet — Version 7.
- No Report Agent narrative yet — Version 8; the ranked table with
  disclosed scores is the deliverable here, not prose explanations.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me a real project's candidates docked against its
  target, ranked by the composite score, with the formula visible and
  at least one 3D pose rendered.
- Summarize what was built and the results of the benchmark sanity
  check if you were able to run one.
