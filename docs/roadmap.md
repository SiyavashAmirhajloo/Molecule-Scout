# Version Roadmap

Build incrementally, same discipline as LexBook-AI, with one added
rule: the vision pipeline (Version 9) is deliberately sequenced late,
after the core product already works on structured data, because it is
the highest-risk, most research-adjacent piece. See `CLAUDE.md` for
the full rationale and time-budget estimates.

## Version 0 — Project Foundation

**Goal:** a professional foundation, including the pieces LexBook-AI
didn't need.

Features:
- GitHub repository, README, Docker setup
- PostgreSQL + pgvector
- **Redis + Celery worker**, wired up with a trivial test task, so the
  background-job pattern is proven before anything real depends on it
- FastAPI backend with clean architecture (api / agents / chem /
  models layering from `docs/requirements.md`)
- Next.js frontend shell
- CI pipeline (lint + build, backend and frontend)

Resume skills demonstrated: Docker, FastAPI, PostgreSQL, Celery/Redis
background job architecture, clean architecture.

## Version 1 — Molecule Knowledge Base

**Goal:** a local, queryable database of known molecules — the
"library" equivalent from LexBook-AI, but for chemistry.

Features:
- Ingest a bulk subset of PubChem and/or ChEMBL (pick a manageable
  slice — e.g. a specific target class or a fixed compound count —
  don't attempt full-database ingestion)
- RDKit-based parsing/validation of every ingested molecule
- Molecule embedding abstraction layer: Morgan/ECFP fingerprints as
  the default
- Store molecules + fingerprints in PostgreSQL/pgvector
- A basic similarity search endpoint: given a SMILES, return the
  nearest known molecules

Resume skills: cheminformatics fundamentals, vector search, embedding
abstraction layers.

## Version 2 — Project Intake & Retrieval

**Goal:** let a user start a real project and get real retrieval
results.

Features:
- Project creation: target (PDB ID) and/or seed molecule (SMILES/name)
- Retrieval Agent: given a project's target/seed, return the most
  relevant known compounds from Version 1's knowledge base, each with
  a citation to its source database entry
- Frontend: project dashboard + retrieval results view

Resume skills: retrieval system design, citation-grounded results.

## Version 3 — Property Filtering Pipeline

**Goal:** get the filtering pipeline solid before adding generative
complexity — this is cheap to build and immediately useful even
without generation, since it can also rank/filter the retrieved known
compounds.

Features:
- RDKit-based QED, SA score, Lipinski's Rule of Five, PAINS filtering
- Apply filters to retrieval results as a first use case
- Frontend: property breakdown shown per compound, sortable/filterable
  comparison table

Resume skills: applied cheminformatics, RDKit fluency.

## Version 4 — Baseline Generative Agent

**Goal:** get a diffusion model actually generating valid molecules
end-to-end, without retrieval conditioning yet — prove the generative
core works before layering the novel retrieval-augmented mechanism on
top.

Features:
- Integrate the chosen diffusion backbone (EDM-style 3D or DiGress-
  style 2D graph — pick one per `docs/tech-stack.md` and document why)
- Train/fine-tune on QM9 or a filtered ZINC subset
- Generation runs as a Celery background job with status polling
- Unconditioned or simple property-conditioned generation only (target
  molecular weight/logP ranges)
- Run and report standard validity/uniqueness/novelty/diversity
  metrics (MOSES/GuacaMol) on generated batches — this is the
  project's first real evaluation checkpoint

Resume skills: diffusion models, generative model evaluation
methodology, background job orchestration for ML inference.

## Version 5 — Retrieval-Augmented Generation

**Goal:** the technical core of the product — condition the diffusion
model on retrieved known compounds.

Features:
- Implement the RetMol-style conditioning mechanism from
  `docs/architecture.md`: project retrieved molecule embeddings into
  the diffusion model's conditioning space, inject during denoising
- Fallback path to plain property-conditioned generation when
  retrieval returns weak/no matches, with that fallback explicitly
  surfaced to the user
- Re-run the Version 4 evaluation suite and compare: does retrieval
  conditioning measurably shift generated candidates closer to known,
  relevant chemical space (e.g. average similarity to the retrieved
  set) without collapsing diversity?

Resume skills: retrieval-augmented generation applied to a non-LLM
generative model, ablation-style evaluation.

## Version 6 — Docking & Composite Ranking

**Goal:** turn generated candidates into ranked, actionable results.

Features:
- AutoDock Vina integration: receptor/ligand prep (Open Babel/
  MGLTools), docking run as a Celery background job
- Composite rank score combining docking affinity, drug-likeness, and
  novelty, per the disclosed formula in `docs/architecture.md`
- Frontend: 3D docking pose viewer (3Dmol.js/NGL), ranked candidate
  table
- Sanity-check the docking setup against a benchmark target with known
  actives/decoys (e.g. a DUD-E target) if one fits the project's scope

Resume skills: molecular docking, transparent composite scoring,
scientific benchmarking discipline.

## Version 7 — Multi-Agent Orchestration via LangGraph

**Goal:** wire the individually-working agents (Retrieval, Property,
Generation, Docking) from Versions 1–6 into a real LangGraph workflow
with a Coordinator, rather than separate endpoints called in sequence
by the frontend.

Features:
- LangGraph implementation of the core stages diagram in
  `docs/architecture.md`
- Coordinator routes new-project, regenerate-candidates, and re-dock
  requests appropriately, re-entering the graph at the right stage
  rather than always starting from scratch
- Tracing/logging of the full graph path, including background job
  stages, via Langfuse

Resume skills: LangGraph multi-agent orchestration over a pipeline
with long-running async steps — a step up from LexBook-AI's mostly-
synchronous agent graph.

## Version 8 — Report Agent & Research Notebook

**Goal:** turn ranked candidates into something a human researcher
would actually want to read, and give the product memory across
sessions.

Features:
- Report Agent: LLM-written plain-English rationale per candidate
  (what it's similar to, why it's promising, what's uncertain),
  explicitly framed as requiring human/wet-lab verification per the
  responsible-use design in `docs/architecture.md`
- Shortlist/save functionality
- Export: SDF for structures, PDF for the full assembled report
- Memory Agent: project history persists across sessions (past
  targets, past candidate sets, saved shortlists)

Resume skills: LLM report generation grounded in structured upstream
data, long-term memory design.

## Version 9 — Vision Agent: Literature Structure Extraction

**Goal:** the differentiating feature — deliberately last among the
core capability versions, since it's the highest-risk piece and
shouldn't gate a working product.

Features:
- PDF ingestion and page rasterization
- Diagram localization (document layout/object detection)
- Structure recognition (DECIMER or MolScribe) producing SMILES with
  confidence scores
- RDKit-based validation of extracted structures
- OCR-based context linking (compound identifiers, nearby activity
  data)
- Deduplication against the existing knowledge base
- Frontend: literature browser, extracted-structure review UI
  (especially for low-confidence extractions)
- Build and maintain a small "golden set" of structure-diagram images
  with known-correct SMILES to regression-test extraction accuracy as
  the pipeline evolves

Resume skills: applied object detection + specialized recognition
models on a genuinely hard, real-world vision problem — directly
extends existing YOLO/segmentation experience into a novel domain.

## Version 10 — Production Hardening & Safety

**Goal:** harden the app to production shape and make the dual-use
safety design from `docs/architecture.md` a real, enforced part of the
system rather than a doc section.

Features:
- Authentication: JWT, Google OAuth, guest mode
- Safety Agent: structural screening against known toxic-scaffold/
  controlled-substance analog libraries, enforced (non-configurable)
  on every generated candidate before it reaches a report
- Rate limiting on generation requests, per user
- Structured logging, centralized error handling, health/readiness
  checks
- Hardened Docker setup (multi-stage builds, non-root users), CI/CD
  deploy pipeline
- Job-queue monitoring/alerting (queue depth, failure rate)

Resume skills: production AI engineering, responsible-AI/dual-use
safety design implemented as enforced system behavior, not policy text.

## Future Versions (post-V10, optional)

- **Pocket-conditioned 3D generation** (DiffSBDD/TargetDiff-style) —
  generate candidates conditioned directly on the target protein's
  binding pocket structure, not just retrieved analogs
- **DiffDock as an alternate docking backend** — a second legitimate
  use of diffusion models in the product (pose prediction instead of
  molecule generation), swappable via the docking abstraction layer
- **Multi-target comparison** — evaluate one candidate set against
  several related targets (e.g. a target family) at once
- **Analytics dashboard** — project-level generation/retrieval/docking
  quality trends over time, mirroring LexBook-AI's V8 dashboard
  philosophy (transparent formulas, no black boxes)
- **Collaborative projects** — multi-user shared projects, in-app
  annotation/discussion on candidates
- **Active learning loop** — feed real (simulated or literature-
  sourced) assay results for shortlisted candidates back into the
  retrieval corpus and generation conditioning

## Presentation Advice

This project's story is stronger than LexBook-AI's in one specific
way: it combines four distinct hard-technology areas (vision,
generative diffusion modeling, retrieval, multi-agent orchestration)
around one coherent, domain-literate product — lead with that framing
in the README and any write-up, and be explicit and upfront about the
responsible-use design; a thoughtful dual-use mitigation section reads
as engineering maturity, not as a caveat to bury in a footnote.
