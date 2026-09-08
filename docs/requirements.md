# Requirements

## Functional Requirements

The application should support:

- Creating a **project** scoped to a target (protein, by PDB ID or
  uploaded structure/FASTA) and/or a seed molecule (by name, SMILES,
  or uploaded structure image)
- Uploading literature/patents (PDF) for a project, or pointing the
  system at open-access sources to ingest
- Viewing extracted structures from ingested literature, each with its
  confidence score, source citation, and (if RDKit parsing failed) a
  flag for manual review
- Browsing retrieved known compounds relevant to the project's target,
  with citations back to their source (database entry or literature
  page)
- Triggering candidate generation, with visible job status (queued /
  running / done / failed) since this runs as a background job
- Viewing generated candidates with: 2D structure rendering, all
  property filter results (QED, SA score, Lipinski, PAINS — pass/fail
  and raw values, not a collapsed flag), docking score, novelty score,
  and the composite rank score with its formula shown
- Viewing a 3D docking pose for any candidate against the target
- Reading the Report Agent's plain-English rationale per candidate
- Saving/starring candidates into a project shortlist
- Exporting a project's shortlist (SDF for structures, PDF for the
  full report)
- Viewing project history: what's been ingested, generated, and
  shortlisted, across sessions

## Non-Functional Requirements

The application should be:

- Modular — each agent independently testable and swappable
  (generation backbone, docking backend, embedding method)
- Asynchronous by design for anything slow — no request should block
  on a diffusion sampling run or a docking job
- Transparent — every score shown to the user must be traceable to a
  disclosed formula or a named benchmark metric; no unexplained
  "confidence: 87%" style outputs
- Reproducible — generation runs should record the model checkpoint
  version and random seed used, so a result can be regenerated
- Safe by construction — the Safety Agent's screening pass (see
  `docs/architecture.md`) is not optional and cannot be disabled via
  configuration
- Well documented, type-safe, and production-shaped, per the same
  standard set on LexBook-AI

## Data & Copyright Handling

Ingested literature/patents are frequently copyrighted. Apply the same
discipline used on LexBook-AI, adapted for structures instead of text:

- Do not retain full-page images beyond the extraction step's
  processing window — persist only the extracted structure (SMILES),
  its confidence score, and citation metadata (source title, page
  number, a link if the source is openly accessible), not the
  rendered page image itself
- Never reproduce substantial verbatim text from a paper/patent in the
  UI or in exported reports — citations point to the source, they
  don't reproduce it
- Where a source is not open-access, store only what's needed to cite
  it (title, authors, identifier), not the document itself

## UI Requirements

- Responsive, dark-mode-capable, consistent with LexBook-AI's design
  language where reasonable, but this product's information density is
  higher — prioritize clear data tables and comparison views over
  decoration
- **Project dashboard** — target/seed summary, ingestion status,
  generation job status, shortlist count
- **Literature browser** — ingested sources, extracted structures per
  source, confidence indicators
- **Retrieval view** — known compounds relevant to the target, with
  citations
- **Candidate comparison table** — sortable/filterable by any property
  or score, with inline 2D structure thumbnails
- **Molecule detail view** — full property breakdown, 3D docking pose
  viewer, Report Agent rationale, save/export actions
- **Job queue view** — visibility into running/queued background jobs,
  since generation and docking are not instant

## Scale

Design with a growth path in mind:

`1 project, 1 user, CPU-only demo → multiple projects, GPU worker for
generation/docking → multi-user, dedicated GPU pool`

## Deliverables (for the initial design phase)

When designing the system, produce:

1. Overall architecture (see `docs/architecture.md`)
2. Folder structure
3. Database schema (see entities below)
4. LangGraph workflow (see `docs/architecture.md`)
5. Background job architecture (Celery task definitions, retry/failure
   handling for each slow step)
6. API design
7. UI architecture
8. Technology choices with justification (see `docs/tech-stack.md`)
9. Security and dual-use safety considerations
10. Deployment strategy (including the CPU/GPU worker split)
11. Future improvements
12. Recommended open-source libraries/models and why
13. Development roadmap divided into milestones (see `docs/roadmap.md`)

## Core Data Entities

- **Project** — target reference(s), seed molecule(s), creation date,
  owner
- **LiteratureSource** — uploaded/ingested document metadata, citation
  info, ingestion status
- **ExtractedStructure** — SMILES, confidence score, source page/
  bounding box reference, linked LiteratureSource, review status
- **KnownMolecule** — canonical structure, source (database or
  extraction), fingerprint/embedding, any linked activity data
- **GeneratedCandidate** — canonical structure, generation job
  reference, model checkpoint/seed used, retrieved-conditioning set
  used
- **PropertyResult** — per-candidate QED, SA score, Lipinski
  breakdown, PAINS flag
- **DockingResult** — per-candidate docking pose, affinity score,
  composite rank score and its formula version
- **Report** — per-candidate rationale text, assembled project report
- **Job** — Celery job metadata: type, status, timestamps, failure
  reason if applicable

## Suggested Folder Structure (high level)

```
frontend/
backend/
  app/
    agents/          # one module per agent
    workers/          # Celery task definitions
    chem/              # RDKit / cheminformatics utilities
    vision/            # structure extraction pipeline
    generation/        # diffusion model abstraction + backbones
    docking/           # docking abstraction + Vina integration
    api/
    models/            # SQLAlchemy models for the entities above
database/
docker/
docs/
tests/
scripts/
.github/
```
