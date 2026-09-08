# Molecule Scout

> Working name — check trademark/domain availability before any public launch.

AI research assistant for early-stage drug discovery. Given a disease target or seed
molecule, it surveys known compounds, proposes novel candidates with a retrieval-
conditioned diffusion model, filters and docks them against the target, and returns
a ranked, explained shortlist. Built as a real product (FastAPI + Celery + pgvector
+ Next.js + LangGraph), not a notebook. **Generated molecules are not validated drug
candidates** — output is a triage aid requiring human/wet-lab verification.

## Status — V0 Foundation ✓

V0 proves the deployable skeleton everything else builds on. No chemistry yet.

| Check | Status |
|---|---|
| `docker compose up --build` boots `api` + `worker` + `db` (pgvector) + `redis` | ✓ |
| `GET /health` reports `{"db": "ok", "redis": "ok"}` | ✓ |
| `POST /jobs/test` → `GET /jobs/{id}` round-trips via Celery (`success`, `result: 3`) | ✓ |
| `pytest` passes (health shape + eager job test) | ✓ |
| `ruff check` clean, `tsc --noEmit` + `next build` clean | ✓ |
| CI runs backend (`ruff` + `pytest`) and frontend (`tsc` + `build`) on push/PR | ✓ |
| Frontend shell renders and fetches `/health` | ✓ |

Next: **V1 — Molecule Knowledge Base** (PubChem/ChEMBL slice, RDKit validation,
Morgan/ECFP fingerprints, pgvector similarity search).

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
  tests/                    # test_health.py, test_jobs.py (eager mode)
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
| V1 | Molecule Knowledge Base | PubChem/ChEMBL slice, RDKit, fingerprints, similarity search |
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
