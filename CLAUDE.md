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

## Tooling & Skill Routing

This section governs which skills, commands, and tools to use for each kind of work in this repository. It is routing guidance only — the product workflow above is unchanged by anything here.

Read the relevant `SKILL.md` before starting work in its domain. Do not guess at a skill's contents from its name.

### Project skills (`.claude/skills/`)

Use these for design and front-end work:

| Skill | Use it for |
|---|---|
| `design-system` | Design tokens, component specs, and slide-system conventions. Read before introducing a new component or color/typography scale. |
| `design` | Logo, icon, banner, and CIP (creative-intelligence-prompt) style guidance. |
| `brand` | Brand guidelines, color-palette management, asset organization, consistency checks. |
| `ui-styling` | Tailwind/CSS styling and canvas design-system conventions. |
| `ui-ux-pro-max` | Stack-specific UI/UX patterns, charts, motion, landing pages, React performance. |
| `slides` | Slide-deck authoring and slide background/chart/copy logic. |
| `banner-design` | Banner sizing and styles. |

### Project skills (`.agents/skills/`)

| Skill | Use it for |
|---|---|
| `frontend-design` | Distinctive, non-templated visual direction for new or reworked UI. Read before writing any UI. |
| `senior-frontend` | Next.js/React performance, component scaffolding, bundle analysis. |
| `vercel-react-best-practices` | React correctness rules (effects, dependency arrays, async patterns). Read before changing hooks or data fetching. |
| `web-design-guidelines` | Web accessibility and interaction guidelines. |
| `sqlalchemy-alembic-expert-best-practices-code-review` | Reviewing schema changes, migrations, indexes, and constraints. |

### Project skills (`.shared/`)

| Skill | Use it for |
|---|---|
| `python-backend` | FastAPI, JWT/OAuth2, SQLAlchemy async, Redis/Upstash caching, rate limiting, API patterns. Read `SKILL.md` and its `references/` directly. |
| `ty-skills` | Python type checking with `ty`, type annotations, `pyproject.toml` type config, editor setup. |
| `commit-message` | Analyze git changes and generate Conventional Commits; use before committing. |
| `excalidraw-ai` | Generate architecture diagrams, flowcharts, and data-flow visuals as Excalidraw JSON directly (no generator script required — see `SKILL.md`). |

### Project commands (`.claude/commands/`)

| Command | Purpose |
|---|---|
| `/kb-search <query>` | Search the `python-backend` knowledge base. **Broken as of 2026-09-23:** `.shared/python-backend/scripts/knowledge_db.py` does not exist on disk. Read `.shared/python-backend/SKILL.md` and `references/` directly until the script is restored. |
| `/kb-get <entry-id>` | Read a full knowledge-base entry. **Broken as of 2026-09-23:** same missing script as `/kb-search`. |
| `/commit-batch` | Suggest logical batch commits for current changes. |
| `/commit-analyze` | Analyze the current diff. |
| `/excalidraw <description>` | Generate an Excalidraw diagram. The command references `excalidraw_generator.py`, which does not exist on disk; follow `.shared/excalidraw-ai/SKILL.md` (JSON-direct method) instead. |
| `/ty-check [path]` | Scan and fix Python type errors with `ty`. |

### Host tools and connectors

These are provided by the host environment, not by this repository. Use them when the task calls for it:

| Tool | Use it for |
|---|---|
| `mcp__exa__web_search_exa` | Web/literature search when building the retrieval corpus or sourcing references. |
| `mcp__colab-mcp__*` | Running GPU code in Colab (diffusion-model training, vision-pipeline experiments). |
| `Read`, `Edit`, `Write`, `Glob`, `grep` | Direct file access and search across the repo. |
| `Bash` | Shell commands. Project commands use `python3` on POSIX or `.venv\Scripts\python` on Windows. |
| `mcp__workspace__bash` | Isolated Linux sandbox; project folder mounts at `/sessions/<session>/mnt/Molecule-Scout`. |
| `mcp__workspace__web_fetch` | Fetch a specific URL. |
| `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` | Track multi-step work. |
| `Agent` | Delegate open-ended exploration; include full context in the prompt. |
| `WebSearch` | Current or post-cutoff information. |
| `mcp__plugins__*` | Discover and suggest plugins for task-specific connectors. |
| `mcp__skills__*` | List or suggest standalone skills. |
| `mcp__cowork__*` | Directory access, file presentation, artifacts, and memory. |
| `mcp__scheduled-tasks__*` | Create/update recurring or one-time scheduled tasks. |

### Skills available in this session but not project-specific

These load automatically via the `Skill` tool by name. Invoke them when the task calls for it:

| Skill | Use it for |
|---|---|
| `anthropic-skills:docx` | Creating, reading, or editing Word documents. |
| `anthropic-skills:pdf` | Any PDF work: reading, creating, merging, OCR, forms. |
| `anthropic-skills:pdf-reading` | Extracting text, tables, or images from PDFs. |
| `anthropic-skills:xlsx` | Spreadsheet work as the primary input or output. |
| `anthropic-skills:pptx` | PowerPoint creation, editing, or reading. |
| `anthropic-skills:frontend-design` | Intentional visual design guidance for new UI. |
| `anthropic-skills:schedule` | Creating or updating scheduled tasks. |
| `anthropic-skills:setup-claude` | Guided plugin/skill/tool setup. |
| `anthropic-skills:consolidate-memory` | Reflective pass over memory files. |
| `anthropic-skills:explain-usage` | Token usage breakdown with a chart. |
| `init` | Initializing a new `CLAUDE.md`. |
| `security-review` | Security review of pending changes. |

### Skills and plugins inventory note

These lists reflect the inventory as of the last audit (2026-09-23), read from the files actually on disk. When a skill's `SKILL.md` is missing, unreadable, or conflicts with this table, the file on disk wins.

Re-audit when a skill or plugin is installed or removed, and when the user asks for a skills audit or a config/CLAUDE.md refresh.

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

Things never to cut: RDKit-based property filtering, docking against
a real target, retrieval with real citations back to source compounds,
transparent/disclosed scoring (no black-box "trust me" scores), the
dual-use safety screening pass described in `docs/architecture.md`,
and an honest README that never implies a generated molecule has been
validated as a real drug candidate.
