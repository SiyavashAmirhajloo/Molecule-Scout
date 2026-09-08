We are starting **Version 2 — Project Intake & Retrieval**, as scoped
in `docs/roadmap.md`. Version 1 (molecule knowledge base, fingerprint
similarity search) is done — review what exists before proceeding.

## Goal

Let a user start a real project around a target and/or seed molecule,
and get back real, citation-backed retrieval results from the
Version 1 knowledge base.

## Scope for this version only

- Project model: a project has a target (PDB ID, stored as a
  reference for now — full structure handling comes with docking in
  Version 6) and/or a seed molecule (SMILES or name, resolved to a
  canonical structure via RDKit)
- Retrieval Agent: given a project's target/seed, query the Version 1
  knowledge base and return the most relevant known compounds
- Every retrieval result must carry a citation back to its source
  (which database, which entry/ID)
- Frontend: a project creation flow and a retrieval results view
  showing structures + citations

## Ground rules

- No literature/PDF ingestion yet — that's Version 9 (Vision Agent),
  deliberately much later. Retrieval in this version only draws from
  the structured Version 1 knowledge base.
- No property filtering yet — Version 3.
- No generation yet — Versions 4–5.
- If a seed molecule is provided, retrieval should reason primarily on
  fingerprint similarity to it; if only a target is provided (no seed
  molecule yet), it's fine for this version to return the target's
  known/annotated ligands if your ingested slice includes any, or to
  clearly state that no compounds are yet associated with that target
  — don't fabricate a retrieval signal that isn't there.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, walk me through a real project creation with a seed
  molecule and show the retrieval results with working citations.
- Summarize what was built and any limitations in how targets are
  currently represented (full protein structure handling isn't due
  until Version 6).
