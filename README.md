# Molecule Scout

> Working name — check trademark/domain availability before any public launch.

AI research assistant for early-stage drug discovery. Given a disease target or seed
molecule, it surveys known compounds, proposes novel candidates with a retrieval-
conditioned diffusion model, filters and docks them against the target, and returns
a ranked, explained shortlist. Built as a real product (FastAPI + Celery + pgvector
+ Next.js), not a notebook. **Generated molecules are not validated drug
candidates** — output is a triage aid requiring human/wet-lab verification.

## Try V6 in five minutes

```bash
docker compose up --build          # api + worker + db + redis + frontend
docker compose exec api python scripts/ingest_chembl.py   # one-shot: 3,417 approved drugs
```

Then open **http://localhost:3000** and walk the loop:

1. **Start a project** — the bench takes a target PDB ID (`1M17` for EGFR) and one
   seed field that accepts *either* a SMILES or a compound name (`ERLOTINIB`
   resolves against the ChEMBL corpus). You land on `/projects/{id}`.
2. **Retrieve** — the first tab lists ChEMBL analogs with similarity, property
   columns, and working citations.
3. **Generate** — the second tab runs diffusion conditioned on the top retrieved
   molecule, showing validity/uniqueness/novelty/diversity and a conditioning
   badge (or the honest fallback reason when retrieval is weak).
4. **Dock** — the third tab docks the candidates against 1M17 and adds Rank /
   Affinity / Score columns plus a formula banner:
   `rank_score = 0.5 * norm_affinity + 0.3 * QED + 0.2 * novelty` (`v6-1`).
5. **Click a ranked row** — the *Finding* drawer beside the table opens the 3D
   pose viewer (3Dmol.js, pinned CDN; a failed load shows a visible error, never
   a blank box).

The tabs are a pipeline, not three stacked tables: one stage is visible at a
time, and the connector above shows where you are.

The same flow over curl (docking three known drugs directly, real numbers from
a live run):

```bash
curl -X POST localhost:8000/projects -H 'Content-Type: application/json' \
  -d '{"pdb_id":"1M17","seed_name":"ERLOTINIB"}'
# → project id, retrieval hits with ChEMBL citations

curl -X POST localhost:8000/projects/<id>/dock -H 'Content-Type: application/json' \
  -d '{"candidate_smiles":["COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
       "COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC",
       "CC(=O)Oc1ccccc1C(=O)O"]}'
# → poll GET /jobs/<job> → ranked rows; expected affinities:
#   gefitinib  ≈ -8.0  (score 0.86)
#   erlotinib  ≈ -7.3  (score 0.66)
#   aspirin    ≈ -5.7  (score 0.37)
# Both real EGFR inhibitors beat aspirin. scores differ if novelty≠1
# (these drugs are IN the ChEMBL corpus, so novelty = 0 for a seeded DB).

curl localhost:8000/projects/<id>/docking/<result_id>
# → pose PDBQT + box center + formula_version, keyed by integer result id
```

Docking sanity check (local venv, needs network + `backend/bin/vina`):

```bash
.venv/Scripts/python backend/scripts/dock_sanity.py --n-actives 15 --n-decoys 30
# DUD-E EGFR, ~25 min: ROC AUC + bootstrap CI + EF@1/5/10 vs achievable max
```

## Status — V6 Docking & Composite Ranking ✓

| Check | Status |
|---|---|
| `docker compose up --build` boots `api` + `worker` + `db` (pgvector) + `redis` + `frontend` | ✓ |
| `GET /health` reports `{"db": "ok", "redis": "ok"}` | ✓ |
| `POST /jobs/test` → `GET /jobs/{id}` round-trips via Celery | ✓ |
| `pytest` — 51 tests, eager Celery, no services needed | ✓ |
| `ruff check` clean, `tsc --noEmit` + `next build` clean | ✓ |
| CI runs backend (`ruff` + `pytest`) and frontend (`tsc` + `build`) on push/PR | ✓ |
| Live E2E: project → generate → dock → ranked table → 3D pose | ✓ |
| DUD-E EGFR smoke: actives enriched at top of ranking (AUC 0.622, CI [0.445, 0.787]) | ✓ (borderline, see below) |

Next: **V7 — Multi-Agent Orchestration** (LangGraph coordinator over the V1–V6
agents, Langfuse tracing).

## Knowledge Base (V1) ✓

Local store of **3,417 approved drugs** ingested from the ChEMBL REST API
(`molecule.json?max_phase=4`, 4,225 records total; 808 had no structure,
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
curl "localhost:8000/molecules/similar?smiles=CC(%3DO)Oc1ccccc1C(%3DO)O&limit=3"
# ASPIRIN 1.0, BENORILATE 0.51, SALICYLIC ACID 0.45
```

## Project Intake & Retrieval (V2) ✓

`POST /projects` with `{pdb_id?, seed_smiles?, seed_name?}` (at least one required).
Retrieval runs inline against the V1 store via `backend/app/agents/retrieval.py`
(shared with `GET /molecules/similar`) and every hit carries
`citation: {database: "ChEMBL", entry_id, url}`.

- `seed_smiles` accepts either a SMILES or a compound name — if it doesn't parse
  as SMILES it is resolved as a name, so the UI needs one field for both
- Seed by name resolves locally against ingested `pref_name`s (substring match, so
  `ERLOTINIB` finds `ERLOTINIB HYDROCHLORIDE`); unknown name → 422
  (no external lookup — corpus boundaries stay honest)
- Target-only (PDB ID, no seed) returns `results: []` with an honest message —
  never fabricated retrieval (V5's generation fallback depends on this distinction)
- `projects` table via Alembic `002` (pdb_id, canonical seed_smiles, seed_source)
- **V6 removed this limitation:** `pdb_id` is now validated
  (`^[0-9][A-Za-z0-9]{3}$`, traversal-safe) and used to fetch + prepare the real
  receptor structure on first dock.

## Property Filtering (V3) ✓

Every retrieval hit carries `properties` computed live by
`backend/app/agents/properties.py` (pure RDKit function — reused for generated
candidates in V4 and every docked candidate in V6):

- **QED** (`rdkit.Chem.QED.qed`) — 0–1 drug-likeness; aspirin 0.550
- **SA score** (`rdkit.Contrib.SA_Score`, Ertl) — 1 (easy) to 10; aspirin 1.58
- **Lipinski** (MW ≤ 500, logP ≤ 5, HBD ≤ 5, HBA ≤ 10) — each component shown,
  `passes` = ≤1 violation
- **PAINS** (480-pattern catalog) — `passes` = zero matches

No server-side thresholds — the API returns the full breakdown and the UI
sorts/filters client-side. QED feeds the V6 rank score directly.
`frontend/app/components/MoleculeTable.tsx` is the shared comparison table:
sortable headers (similarity, QED, SA, MW, logP, and V6's affinity/score) +
filters (min QED, max SA, Lipinski-only, PAINS-free).

## Baseline Generation (V4) ✓

Real 2D graph diffusion, not a placeholder. **Backbone: Graph-DiT**
(`torch-molecule`, NeurIPS 2024) trained on **QM9** — chosen over EDM-3D because
CPU sampling is feasible, MW/logP conditioning is native, and 2D fits V5's
conditioning paths; see `docs/tech-stack.md` for the full tradeoff.

- Train on free Colab T4 via `notebooks/train_graphdit_qm9.ipynb`, export `.pt`;
  worker runs **CPU-only torch** + `torch-molecule`, loads checkpoint from
  `models/graphdit-qm9.pt` (`GENERATOR_CHECKPOINT` overrides, gitignored)
- `GeneratorBackend` Protocol (`backend/app/generation/base.py`) keeps diffusion
  swappable; `GraphDiTBackend` is the real provider
- `POST /jobs/generate {n, mw_min/max, logp_min/max, seed}` → Celery task →
  `GET /jobs/{id}` poll; every candidate gets V3 `properties`; each run records
  `{checkpoint: "graphdit-qm9/<sha>", seed}`
- Metrics computed directly (no MOSES dep): validity, uniqueness, novelty (vs
  `known_molecules`), diversity (1 − mean pairwise Tanimoto)

**Baseline numbers** (checkpoint `graphdit-qm9/21ff440fa37f`, Graph-DiT 100 epochs
on QM9/133,885, Colab T4; sampled CPU, n=20, seed 42, ~63s): validity **0.75**,
uniqueness **1.0**, novelty **1.0** (vs 3,417-drug corpus), diversity **0.935**.
Caveat: QM9 caps at 9 heavy atoms, so candidates are small
fragments (e.g. `OCC(O)N1CCC1`, QED 0.487) — expected, not a defect.

## Retrieval-Augmented Generation (V5) ✓

The V4 checkpoint is unconditional (`task_type=[]`, verified in weights), so
guidance-vector injection is impossible without retraining. V5 uses **seed-graph
init** instead: the top retrieved molecule's graph is forward-noised to step
`noise_steps`, then denoised through the real loop
(`backend/app/generation/conditioned.py`). Lighter-touch path sanctioned by
`docs/architecture.md`; ablatable via the `noise_steps` knob.

- `POST /projects/{id}/generate {n, noise_steps=100, seed}`: re-runs retrieval,
  gates on `RETRIEVAL_CONDITION_MIN_TANIMOTO = 0.3` (named, disclosed), returns
  `conditioning: {mode, seed_smiles?, similarity?}` — `retrieval-conditioned` or
  `fallback-unconditioned` with reason, never silent
- Task computes `avg_similarity_to_seed` alongside V4 metrics; frontend shows a
  conditioning badge + sim-to-seed
- Projects without a seed molecule get 422 (fallback path is for weak retrieval,
  not absent seeds)

| Run (ASPIRIN seed, n=20, seed 42) | Validity | Uniq | Nov | Diversity | Sim-to-seed |
|---|---|---|---|---|---|
| V4 unconditioned (baseline) | 0.75 | 1.0 | 1.0 | 0.935 | n/a |
| V5 conditioned, k=100 | 0.80 | 1.0 | 1.0 | 0.928 | 0.079 |
| V5 conditioned, k=50 | 0.30 | 1.0 | 1.0 | 0.868 | 0.128 |

Honest reading: the knob works (lower k → closer to seed: 0.079 → 0.128) without
collapsing diversity, but absolute similarities stay low — QM9-fragment outputs
can't get structurally close to a drug-sized seed like aspirin. The mechanism is
proven; its visible effect is bounded by the backbone's molecule size.

## Docking & Composite Ranking (V6) ✓

Turns candidates into ranked, actionable results.

- **AutoDock Vina 1.2.7** — official release binary provisioned by
  `backend/scripts/fetch_vina.py` (pinned SHA-256 per platform, idempotent;
  pip `vina` package unused — no Windows wheels). Subprocess path in local dev
  and Docker alike, so there is exactly one docking code path. `--cpu 2` so
  Vina doesn't starve the Celery worker.
- **Meeko PDBQT prep** — maintained MGLTools successor, pip-installable, handles
  the altloc residues 1M17 needs (A:751/A:831) via `--default_altloc A`.
  Deviation from the Open Babel/MGLTools named in `docs/tech-stack.md`,
  recorded there in this version.
- **Co-crystal pocket only** — box centers on the largest credible HETATM ligand;
  sulfates, ions, glycerol, and modified residues (MSE/SEP/TPO/PTR) are excluded.
  No ligand → 422 with the exact message *"docking refused rather than guessing"*.
  Fixed 20Å cube.
- **Composite rank score** — `rank_score = 0.5 * norm_affinity + 0.3 * QED +
  0.2 * novelty` (`formula_version = "v6-1"`). Disclosed in API, UI, and every
  persisted row; shown next to the number, never as a bare score.
- **`DockingResult` persistence** (Alembic `003`) — pose, affinity, novelty,
  score, formula version, box center per candidate, keyed by integer id for the
  pose viewer (`SMILES is never a URL key` — `/`, `#`, `\`).
- **3D pose viewer** — 3Dmol.js via pinned CDN (v2.4.0) + SRI hash; a failed
  load shows a visible error.
- **Trust-boundary caps** — 50 candidates/request, 100 heavy atoms/molecule,
  ETKDG pre-filtered so a pathological embed can't hang a worker.

```bash
python backend/scripts/dock_sanity.py   # DUD-E EGFR smoke test
# 15 actives + 30 decoys, seed 42, ~25 min on CPU
# ROC AUC = 0.622, bootstrap 95% CI [0.445, 0.787], gate 0.7
# EF@1 3.00 (max 3.00) · EF@5 1.80 (max 3.00) · EF@10 1.20 (max 3.00)
```

What that result means: actives are enriched at the top (EF@1 hits 1/1, EF@5
3/5) and the CI crosses the 0.7 gate, but the point estimate sits below it.
**This is a smoke test, not a benchmark** — our 1:4 active:decoy ratio is far
from DUD-E's ~1:60 where EF is most meaningful, and Vina's per-target DUD-E
performance is modest anyway. A fail means check the bounding box, then receptor
prep, then protonation — in that order. The gate is fixed in advance and is not
adjusted to pass.

**Limitations (disclosed, not hidden):**
- `rank_score` is **batch-relative** — min-max normalized within one docking
  run. Comparable inside a batch, never across projects or runs.
- A batch of one always gets norm_affinity = 1.0 (a free 0.5 of rank score).
- Altloc residues resolve to **conformer A** — a modeling choice, not neutral.
- Novelty = 1 − max Tanimoto vs the ChEMBL corpus: known drugs dock with
  novelty 0.0, generated fragments near 1.0.
- DiffDock alternate backend = post-V10 (roadmap "Future Versions").

## Quick Start

Prerequisites: Docker + Docker Compose.

```bash
docker compose up --build
docker compose exec api python scripts/ingest_chembl.py   # first time only
```

- **Frontend:** http://localhost:3000 (bench → project pipeline → pose)
- **API:** http://localhost:8000/docs — `GET /health`, `POST /projects`,
  `GET /projects/{id}`, `POST /projects/{id}/generate`, `POST /projects/{id}/dock`,
  `GET /projects/{id}/docking`, `GET /projects/{id}/docking/{resultId}`, `GET /jobs/{id}`
- **Postgres (pgvector):** `localhost:5432` (`postgres`/`postgres`/`moleculescout`)
- **Redis:** `localhost:6379`

Verify without Docker (backend tests use eager Celery, no services needed):

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/Scripts/python -m pytest backend/tests -v
```

Provision the Vina binary locally (idempotent, checksum-verified):

```bash
.venv/Scripts/python backend/scripts/fetch_vina.py
```

## Project Structure

```
docker-compose.yml           # api + worker + db (pgvector) + redis + frontend
backend/
  Dockerfile                 # python:3.13-slim, non-root, fetches Vina at build
  requirements.txt           # includes meeko + gemmi (PDBQT prep)
  app/
    main.py                  # FastAPI factory + /health (DB + Redis probes)
    config.py                # Pydantic settings (DATABASE_URL, REDIS_URL)
    db.py                    # async SQLAlchemy
    agents/
      retrieval.py           # seed resolution + Tanimoto retrieval + citations
      properties.py          # QED / SA / Lipinski / PAINS (pure RDKit)
    api/
      projects.py            # create / generate / dock / pose-by-id endpoints
      jobs.py, molecules.py  # job polling, similarity search
    docking.py               # V6: receptor fetch+prep, Vina runner, rank_batch
    generation/
      graphdit.py            # V4 Graph-DiT backend (checkpoint)
      conditioned.py         # V5 seed-graph init
      evaluate.py            # validity/uniqueness/novelty/diversity
    workers/
      celery_app.py          # Celery (Redis broker/backend)
      tasks.py               # add / generate_molecules / dock_molecules
    models/                  # known_molecules, projects, docking_results
  alembic/versions/          # 001 known_molecules, 002 projects, 003 docking
  scripts/
    ingest_chembl.py         # one-shot ChEMBL max_phase=4 seed
    fetch_vina.py            # pinned-SHA256 Vina binary provisioning
    dock_sanity.py           # DUD-E EGFR smoke test
    verify_e2e_live.py       # live-stack E2E verification
  bin/                       # vina binary (gitignored, script-managed)
  tests/                     # 51 tests incl. docking (Vina mocked in CI)
frontend/
  app/
    page.tsx                 # landing bench: PDB ID + single seed field
    projects/[id]/page.tsx   # project bench: time-ordered pipeline (Retrieve → Generate → Dock)
  app/components/
    MoleculeTable.tsx        # shared comparison table (V3/V4/V5/V6 columns, affinity/score when docked)
    PoseViewer.tsx           # 3Dmol.js pose viewer (pinned CDN + SRI, renders in the Finding drawer)
.github/workflows/ci.yml     # backend + frontend jobs
docs/                        # tech-stack, architecture, requirements, roadmap
prompts/                     # version-scoped build prompts (V1–V10)
```

## Roadmap

| Version | Goal | Key Deliverable |
|---|---|---|
| **V0** | Foundation | Compose stack + health + job queue + shell + CI |
| **V1** | Molecule Knowledge Base | 3,417 ChEMBL approved drugs, RDKit, fingerprints, similarity search |
| **V2** | Project Intake & Retrieval | Retrieval Agent with citations |
| **V3** | Property Filtering | QED/SA/Lipinski/PAINS |
| **V4** | Baseline Generation | Diffusion backbone, background jobs, eval metrics |
| **V5** | Retrieval-Augmented Generation | RetMol-style conditioning |
| **V6** | Docking & Ranking | AutoDock Vina, composite score, 3D pose viewer |
| V7 | Multi-Agent Orchestration | LangGraph + Langfuse |
| V8 | Report & Notebook | LLM rationales, shortlist, exports |
| V9 | Vision Agent | Literature structure extraction (highest-risk, last) |
| V10 | Hardening & Safety | Auth, Safety Agent, rate limiting, observability |

See `docs/roadmap.md` for the full plan and `docs/tech-stack.md` for mandated choices.

## Tech Stack

Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Celery + Redis,
PostgreSQL + pgvector, Next.js 14 + TypeScript + Tailwind. Cheminformatics:
RDKit (properties/fingerprints), Meeko (PDBQT prep), AutoDock Vina 1.2.7
(subprocess). Generation: Graph-DiT via `torch-molecule` (CPU sampling).
LangGraph/Langfuse arrive with V7.

## License

See [LICENSE](LICENSE).
