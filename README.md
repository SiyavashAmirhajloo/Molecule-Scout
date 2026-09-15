# Molecule Scout

> Working name — check trademark/domain availability before any public launch.

AI research assistant for early-stage drug discovery. Given a disease target or seed
molecule, it surveys known compounds, proposes novel candidates with a retrieval-
conditioned diffusion model, filters and docks them against the target, and returns
a ranked, explained shortlist. Built as a real product (FastAPI + Celery + pgvector
+ Next.js + LangGraph), not a notebook. **Generated molecules are not validated drug
candidates** — output is a triage aid requiring human/wet-lab verification.

## Status — V5 Retrieval-Augmented Generation ✓

V4 proved diffusion generation with baselines. V5 conditions it on retrieval:
seed-graph init (denoise from the top retrieved molecule's noised graph) via
`POST /projects/{id}/generate`, with explicit fallback below 0.3 Tanimoto.

| Check | Status |
|---|---|
| `docker compose up --build` boots `api` + `worker` + `db` (pgvector) + `redis` | ✓ |
| `GET /health` reports `{"db": "ok", "redis": "ok"}` | ✓ |
| `POST /jobs/test` → `GET /jobs/{id}` round-trips via Celery (`success`, `result: 3`) | ✓ |
| `pytest` passes (health shape + eager job test) | ✓ |
| `ruff check` clean, `tsc --noEmit` + `next build` clean | ✓ |
| CI runs backend (`ruff` + `pytest`) and frontend (`tsc` + `build`) on push/PR | ✓ |
| Frontend shell renders and fetches `/health` | ✓ |

Next: **V6 — Docking & Composite Ranking** (AutoDock Vina, disclosed rank formula, 3D pose viewer).

## Knowledge Base (V1) ✓

Local store of **3,417 approved drugs** ingested 2026-09-09 from the ChEMBL REST
API (`molecule.json?max_phase=4`, 4,225 records total; 808 had no structure,
0 failed RDKit parsing, 0 duplicate canonical SMILES). Chosen because approved
drugs are a defensible, citable, target-agnostic retrieval baseline — the
"similar to known drug X" story in later reports is grounded in something real.

- RDKit parses/validates every molecule; `MoleculeEmbedder` Protocol
  (`backend/app/chem/embeddings.py`) with Morgan/ECFP4 (radius 2, 2048 bits)
  default, swappable for a learned embedding later
- `known_molecules` table via Alembic (`backend/alembic/versions/`, upgraded at
  API startup): canonical SMILES (unique), ChEMBL ID, name, `vector(2048)`
  fingerprint
- `GET /molecules/similar?smiles=...&limit=10` — exact Tanimoto over stored
  fingerprints (brute-force over ~3.4k rows; pgvector ordering if it grows)

```bash
docker compose up --build
docker compose exec api python scripts/ingest_chembl.py   # one-shot seed
curl "localhost:8000/molecules/similar?smiles=CC(%3DO)Oc1ccccc1C(%3DO)O&limit=3"
# ASPIRIN 1.0, BENORILATE 0.51, SALICYLIC ACID 0.45
```

## Project Intake & Retrieval (V2) ✓

`POST /projects` with `{pdb_id?, seed_smiles?, seed_name?}` (at least one required;
seed by SMILES or by local drug name, not both). Retrieval runs inline against the
V1 store via `backend/app/agents/retrieval.py` (shared with `GET /molecules/similar`)
and every hit carries `citation: {database: "ChEMBL", entry_id, url}`.

- Seed by name resolves locally against ingested `pref_name`s; unknown name → 422
  (no external lookup — corpus boundaries stay honest)
- Target-only (PDB ID, no seed) returns `results: []` with an honest message —
  never fabricated retrieval (V5's generation fallback depends on this distinction)
- `projects` table via Alembic `002` (pdb_id, canonical seed_smiles, seed_source)

**Limitation:** `pdb_id` is a stored reference string only — no structure fetch,
no pocket handling. Full protein structure handling arrives with docking (V6).

```bash
curl -X POST localhost:8000/projects -H 'Content-Type: application/json' \
  -d '{"seed_name":"ASPIRIN","limit":3}'
# seed_resolved: CC(=O)Oc1ccccc1C(=O)O; ASPIRIN 1.0 + BENORILATE + SALICYLIC ACID,
# each with a working https://www.ebi.ac.uk/chembl/explore/compound/CHEMBL… link
```

## Property Filtering (V3) ✓

Every retrieval hit carries `properties` computed live by
`backend/app/agents/properties.py` (pure RDKit function — reused as-is for
generated candidates in V4; no migration, nothing persisted):

- **QED** (`rdkit.Chem.QED.qed`) — 0–1 drug-likeness; aspirin 0.550
- **SA score** (`rdkit.Contrib.SA_Score`, Ertl, rdkit 2026.03.6) — 1 (easy) to 10;
  aspirin 1.58
- **Lipinski** (MW ≤ 500, logP ≤ 5, HBD ≤ 5, HBA ≤ 10) — each component shown,
  `passes` = ≤1 violation
- **PAINS** (480-pattern catalog) — `passes` = zero matches

No server-side thresholds — the API returns the full breakdown and the UI
sorts/filters client-side. Cutoffs arrive in V6 as a pre-docking gate.
`frontend/app/components/MoleculeTable.tsx` is the shared comparison table:
sortable headers (similarity, QED, SA, MW, logP) + filters (min QED, max SA,
Lipinski-only, PAINS-free). Generic rows (optional `similarity`/`citation`) so
V4's generation view reuses it unchanged.

## Baseline Generation (V4) ✓

Real 2D graph diffusion, not a placeholder. **Backbone: Graph-DiT**
(`torch-molecule`, NeurIPS 2024) trained on **QM9** — chosen over EDM-3D because
CPU sampling is feasible, MW/logP conditioning is native, and 2D fits V5's
conditioning paths; see `docs/tech-stack.md` for the full tradeoff.

- Train on free Colab T4 via `notebooks/train_graphdit_qm9.py`, export `.pt`;
  worker runs **CPU-only torch** + `torch-molecule`, loads checkpoint from
  `models/graphdit-qm9.pt` (`GENERATOR_CHECKPOINT` overrides, gitignored)
- `GeneratorBackend` Protocol (`backend/app/generation/base.py`) keeps diffusion
  swappable; `GraphDiTBackend` is the real provider (no fragment fallback shipped)
- `POST /jobs/generate {n, mw_min/max, logp_min/max, seed}` → Celery task →
  `GET /jobs/{id}` poll (queued/running/done/failed); every candidate gets V3
  `properties`; each run records `{checkpoint: "graphdit-qm9/<sha>", seed}`
- Metrics computed directly (no MOSES dep): validity, uniqueness, novelty (vs
  `known_molecules`), diversity (1 − mean pairwise Tanimoto)
- Frontend "Generate candidates" section reuses `MoleculeTable` unchanged + metrics line

```bash
curl -X POST localhost:8000/jobs/generate -H 'Content-Type: application/json' \
  -d '{"n":20,"seed":42}'
# poll GET /jobs/<id> → candidates + metrics + checkpoint
```

**Baseline numbers** (checkpoint `graphdit-qm9/21ff440fa37f`, Graph-DiT 100 epochs
on QM9/133,885, Colab T4; sampled CPU, n=20, seed 42, ~63s): validity **0.75**,
uniqueness **1.0**, novelty **1.0** (vs 3,417-drug corpus), diversity **0.935**.
Caveat: QM9 caps at 9 heavy atoms, so candidates are small
fragments (e.g. `OCC(O)N1CCC1`, QED 0.487) — expected, not a defect.

## Retrieval-Augmented Generation (V5) ✓

The V4 checkpoint is unconditional (`task_type=[]`, verified in weights), so
guidance-vector injection is impossible without retraining — and retraining
conditional would condition on property vectors, not molecule identity. V5 uses
**seed-graph init** instead: the top retrieved molecule's graph is forward-noised
to step `noise_steps`, then denoised through the real loop
(`backend/app/generation/conditioned.py`). Lighter-touch path sanctioned by
`docs/architecture.md`; ablatable via the `noise_steps` knob.

- `POST /projects/{id}/generate {n, noise_steps=100, seed}`: re-runs retrieval,
  gates on `RETRIEVAL_CONDITION_MIN_TANIMOTO = 0.3` (named, disclosed), returns
  `conditioning: {mode, seed_smiles?, similarity?}` — `retrieval-conditioned` or
  `fallback-unconditioned` with reason, never silent
- Task computes `avg_similarity_to_seed` (mean Tanimoto of valid outputs to the
  seed) alongside V4 metrics; frontend shows a conditioning badge + sim-to-seed
- Projects without a seed molecule get 422 (fallback path is for weak retrieval,
  not absent seeds — target-only projects already answer honestly in V2)

| Run (ASPIRIN seed, n=20, seed 42) | Validity | Uniq | Nov | Diversity | Sim-to-seed |
|---|---|---|---|---|---|
| V4 unconditioned (baseline) | 0.75 | 1.0 | 1.0 | 0.935 | n/a |
| V5 conditioned, k=100 | 0.80 | 1.0 | 1.0 | 0.928 | 0.079 |
| V5 conditioned, k=50 | 0.30 | 1.0 | 1.0 | 0.868 | 0.128 |

Honest reading: the knob works (lower k → closer to seed: 0.079 → 0.128) without
collapsing diversity, but absolute similarities stay low — QM9-fragment outputs
can't get structurally close to a drug-sized seed like aspirin. The mechanism is
proven; its visible effect is bounded by the backbone's molecule size. A larger
backbone (ZINC-scale, V4-future) is what would make the shift dramatic.

## Quick Start

Prerequisites: Docker + Docker Compose.

```bash
docker compose up --build
```

- API: http://localhost:8000 — `GET /health`, `POST /jobs/test`, `GET /jobs/{id}`
- Frontend: run separately `npm --prefix frontend install && npm --prefix frontend run dev` → http://localhost:3000
- Postgres (pgvector): `localhost:5432` (`postgres`/`postgres`/`moleculescout`)
- Redis: `localhost:6379`

Verify without Docker (backend tests use eager Celery, no services needed):

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/Scripts/python -m pytest backend/tests -v
```

## Project Structure

```
docker-compose.yml          # api + worker + db (pgvector/pgvector:pg16) + redis
backend/
  Dockerfile                # python:3.13-slim, non-root user
  requirements.txt
  app/
    main.py                 # FastAPI factory + /health (DB + Redis probes)
    config.py               # Pydantic settings (DATABASE_URL, REDIS_URL)
    db.py                   # async SQLAlchemy + CREATE EXTENSION vector
    api/jobs.py             # POST /jobs/test, GET /jobs/{id}
    workers/celery_app.py   # Celery (Redis broker/backend)
    workers/tasks.py        # add(a, b) — proves the background-job loop
  tests/                    # test_health.py, test_jobs.py (eager mode), test_chem.py
  alembic/                  # env.py + versions/ (001 known_molecules), upgraded at startup
  scripts/ingest_chembl.py  # one-shot ChEMBL max_phase=4 seed
frontend/
  app/page.tsx              # health shell (fetches NEXT_PUBLIC_API_URL/health)
  app/layout.tsx, globals.css, tailwind.config.js, next.config.mjs
.github/workflows/ci.yml    # backend + frontend jobs
docs/                       # tech-stack.md, architecture.md, requirements.md, roadmap.md
prompts/                    # version-scoped build prompts (V1–V10)
```

## Roadmap

| Version | Goal | Key Deliverable |
|---|---|---|
| **V0** | Foundation | Compose stack + health + job queue + shell + CI |
| **V1** | Molecule Knowledge Base | 3,417 ChEMBL approved drugs, RDKit, fingerprints, similarity search |
| V2 | Project Intake & Retrieval | Retrieval Agent with citations |
| V3 | Property Filtering | QED/SA/Lipinski/PAINS |
| V4 | Baseline Generation | Diffusion backbone, background jobs, MOSES/GuacaMol metrics |
| V5 | Retrieval-Augmented Generation | RetMol-style conditioning |
| V6 | Docking & Ranking | AutoDock Vina, composite score |
| V7 | Multi-Agent Orchestration | LangGraph + Langfuse |
| V8 | Report & Notebook | LLM rationales, shortlist, exports |
| V9 | Vision Agent | Literature structure extraction (highest-risk, last) |
| V10 | Hardening & Safety | Auth, Safety Agent, rate limiting, observability |

See `docs/roadmap.md` for the full plan and `docs/tech-stack.md` for mandated choices.

## Tech Stack (V0)

Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Celery + Redis, PostgreSQL + pgvector (`pgvector/pgvector:pg16`), Next.js 14 + TypeScript + Tailwind. RDKit/LangGraph/Diffusion/Docking arrive with the versions that need them — not before.

## License

See [LICENSE](LICENSE).
