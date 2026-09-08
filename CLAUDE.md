# Molecule Scout — Project Guide

> Working name: **Molecule Scout** (replace with a final name later —
> check trademark/domain availability before committing publicly).

## Elevator Pitch

Molecule Scout is an AI research assistant for early-stage drug
discovery. Given a disease target or a seed molecule, it surveys what
is already known — including structures buried as images inside
scientific papers and patents, which most tools can't read — retrieves
the most relevant known compounds, proposes novel candidate molecules
using a retrieval-conditioned diffusion model, filters and docks the
candidates against the target, and hands back a ranked, explained
shortlist instead of a wall of SMILES strings.

It is not a claim to discover real drugs. It is a faithful,
benchmark-honest replication of the pattern real computational
chemistry teams use — literature mining → retrieval → generative
proposal → filtering → docking → triage — built as a real, usable
product rather than a research script.

## Why This Project (and Why It's Different)

Most "AI drug discovery" portfolio projects stop at "generate some
molecules and show pretty pictures." Molecule Scout is deliberately
scoped to avoid that trap:

- It uses the field's actual evaluation standards (QED, SA score,
  Lipinski's Rule of Five, PAINS filtering, MOSES/GuacaMol benchmark
  metrics, AutoDock Vina docking scores) instead of vibes.
- It solves a real, acknowledged problem: chemical literature and
  patents overwhelmingly encode structures as *images*, not
  machine-readable text. A vision pipeline that extracts structure
  from those images is what lets the retrieval corpus include
  everything in the literature, not just what's already sitting in
  structured databases like PubChem or ChEMBL. This is a legitimate,
  hard computer vision problem (detection + structure recognition),
  not a decorative add-on.
- Retrieval-augmented generation isn't LLM-specific here — it's used
  literally, in the RetMol sense: retrieved molecules condition a
  diffusion model's denoising process, the same shape as RAG for text
  but applied to molecular generation.
- It is built and orchestrated as a real multi-agent product —
  LangGraph coordination, a background job queue for slow steps
  (generation, docking), a proper backend, and a UI a chemist could
  actually use — not a Jupyter notebook.

## Main Goals

- Build a genuinely novel, technically deep portfolio product that
  demonstrates computer vision, generative modeling (diffusion),
  retrieval/RAG, and multi-agent orchestration in one coherent system
- Apply real domain rigor (chemistry-level literacy, standard
  cheminformatics benchmarks) so the project holds up under scrutiny
  from people who actually work in computational chemistry
- Produce a live, demoable product — not a repo of experiment scripts
- Practice production AI engineering patterns that transfer directly
  to a job search: async backends, background job orchestration,
  swappable model backends, observability, and responsible-use design

## Core Workflow

1. **Intake.** The user starts a project around a target: a protein
   (by PDB ID or FASTA sequence) and/or a seed molecule (by name,
   SMILES, or a sketched/uploaded structure image).
2. **Literature mining (Vision Agent).** The system ingests relevant
   papers/patents (uploaded by the user or pulled from open sources),
   locates molecular structure diagrams on each page, and converts
   each diagram into a machine-readable structure (SMILES) with a
   confidence score.
3. **Knowledge base construction (Retrieval Agent).** Every known
   molecule — from structured databases (PubChem, ChEMBL) and from
   the vision pipeline's extractions — is embedded and indexed.
   Given the target/seed, the system retrieves the most structurally
   and functionally relevant known compounds, with citations back to
   their source.
4. **Candidate generation (Generation Agent).** A diffusion model,
   conditioned on the retrieved analogs (RetMol-style retrieval-
   augmented conditioning), proposes novel candidate molecules.
5. **Filtering (Property Agent).** Candidates are screened against
   drug-likeness and safety heuristics (QED, SA score, Lipinski,
   PAINS) before anything expensive happens.
6. **Docking & ranking (Docking Agent).** Surviving candidates are
   docked against the target protein (AutoDock Vina baseline) and
   ranked by a transparent, disclosed composite score.
7. **Reporting (Report Agent).** An LLM writes a plain-English
   rationale per surviving candidate — what it's similar to, why it
   might be promising, and what remains uncertain — assembled into a
   shareable, exportable report.

All of this is orchestrated through a LangGraph multi-agent workflow,
with slow steps (structure extraction, generation, docking) running as
background jobs so the product stays responsive.

## How to Use These Docs

- `docs/tech-stack.md` — mandated technology choices, by layer,
  including the cheminformatics- and vision-specific stack this
  project needs beyond LexBook-AI's
- `docs/architecture.md` — the multi-agent design, the retrieval-
  augmented diffusion mechanism, the vision pipeline, the data model,
  evaluation methodology, and the responsible-use/safety design
- `docs/requirements.md` — functional & non-functional requirements,
  UI requirements, data/copyright handling, deliverables
- `docs/roadmap.md` — the version-by-version build plan, sequenced so
  the highest-risk piece (the vision pipeline) doesn't gate a working
  core product

## Guiding Principle: Build in Versions, De-Risk the Hard Part Last

This is a bigger, more ambitious project than a typical portfolio
piece — treat it with the same version discipline that worked for
LexBook-AI, with one additional rule specific to this project:
**prove the core retrieval → generate → filter → dock → report loop
works end-to-end using already-structured data (PubChem/ChEMBL)
before touching the vision pipeline.** The vision pipeline (reading
structures out of literature images) is the most novel and most
differentiating part of the product, but it is also genuinely hard
research-adjacent work. If it's built first and turns out harder than
expected, the whole project stalls with nothing to show. Build it once
there's already a working, demoable product underneath it.

Rough time expectations (working consistently, solo, building on the
FastAPI/LangGraph/Docker fluency already developed on LexBook-AI):
- Working core loop on structured data only (no vision): 4–6 weeks
- Structured data + docking + multi-agent orchestration, demoable:
  8–10 weeks
- Vision pipeline added, full product: 4–6 additional months
- Production-hardened, safety-screened, polished product: 8–12 months
  total

Things intentionally postponed unless truly needed: training a
diffusion model completely from scratch on proprietary data (use and
fine-tune existing open architectures/checkpoints instead), 3D
pocket-conditioned generation (DiffSBDD/TargetDiff-style — a strong
"Future Versions" item, not a v1 requirement), ML-based docking
(DiffDock) as anything but an optional alternate backend, multi-tenant
SaaS, mobile app, wet-lab integration of any kind.

Things never to cut: RDKit-based property filtering, docking against a
real target, retrieval with real citations back to source compounds,
transparent/disclosed scoring (no black-box "trust me" scores), the
dual-use safety screening pass described in `docs/architecture.md`,
and an honest README that never implies a generated molecule has been
validated as a real drug candidate.
