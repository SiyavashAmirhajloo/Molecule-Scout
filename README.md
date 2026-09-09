# Molecule Scout

> Working name — check trademark/domain availability before any public launch.

AI research assistant for early-stage drug discovery. Given a disease target or seed
molecule, it surveys known compounds, proposes novel candidates with a retrieval-
conditioned diffusion model, filters and docks them against the target, and returns
a ranked, explained shortlist. Built as a real product (FastAPI + Celery + pgvector
+ Next.js + LangGraph), not a notebook. **Generated molecules are not validated drug
candidates** — output is a triage aid requiring human/wet-lab verification.

## Status — V1 Knowledge Base ✓

V0 proved the deployable skeleton. V1 adds the queryable molecule store.

| Check | Status |
|---|---|
| `docker compose up --build` boots `api` + `worker` + `db` (pgvector) + `redis` | ✓ |
| `GET /health` reports `{"db": "ok", "redis": "ok"}` | ✓ |
| `POST /jobs/test` → `GET /jobs/{id}` round-trips via Celery (`success`, `result: 3`) | ✓ |
| `pytest` passes (health shape + eager job test) | ✓ |
| `ruff check` clean, `tsc --noEmit` + `next build` clean | ✓ |
| CI runs backend (`ruff` + `pytest`) and frontend (`tsc` + `build`) on push/PR | ✓ |
| Frontend shell renders and fetches `/health` | ✓ |

Next: **V2 — Project Intake & Retrieval**.

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
