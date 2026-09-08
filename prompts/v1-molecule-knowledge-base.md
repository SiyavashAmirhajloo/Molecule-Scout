We are starting **Version 1 — Molecule Knowledge Base**, as scoped in
`docs/roadmap.md`. Version 0 (foundation, including the Celery/Redis
background-job setup) is done — review what exists in the repo before
proceeding. Re-read the "Cheminformatics Stack" section in
`docs/tech-stack.md`.

## Goal

Build a local, queryable database of known molecules — the foundation
everything else (retrieval, generation conditioning, evaluation) will
sit on top of.

## Scope for this version only

- Pick a manageable slice to ingest from PubChem and/or ChEMBL (e.g. a
  specific target class, or a fixed compound count in the low
  thousands) — do not attempt full-database ingestion. Document
  exactly what slice you chose and why.
- Parse and validate every ingested molecule with RDKit; reject or
  flag anything that fails to parse
- Implement the molecule embedding abstraction layer described in
  `docs/tech-stack.md`, starting with Morgan/ECFP fingerprints as the
  default provider, but keep the interface swappable for a learned
  embedding later
- Store molecules + fingerprints in PostgreSQL/pgvector
- A basic similarity search endpoint: given a SMILES string, return
  the nearest known molecules by fingerprint similarity

## Ground rules

- No project/target intake or retrieval-by-target yet — that's
  Version 2. This version just needs to prove the knowledge base and
  similarity search work.
- No property filtering (QED/SA/Lipinski/PAINS) yet — Version 3.
- Keep the embedding provider swappable through the abstraction layer,
  not hardcoded to fingerprints.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- Write the cheminformatics round-trip tests described in
  `docs/tech-stack.md` (SMILES → RDKit → fingerprint → back) as part
  of this version, not deferred.
- When done, show me a real end-to-end test: ingest the chosen slice,
  confirm the count and a few sample records, then run a similarity
  search against a known molecule and show the nearest neighbors.
- Summarize what was built and how big the ingested slice ended up
  being.
