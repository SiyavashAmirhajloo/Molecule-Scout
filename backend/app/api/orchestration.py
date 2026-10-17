"""Pipeline run endpoints: submit and poll.

POST /projects/{id}/run — start a pipeline run (route + params)
GET  /projects/{id}/run/{run_id} — poll (re-checks a waiting job, replays a
     double-resume safely, returns the same payload as POST)
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import db
from app.db import get_session

router = APIRouter()


class RunRequest(BaseModel):
    route: str = Field(description="new_project | regenerate | redock | full_rerun")
    n: int | None = Field(default=None, ge=1, le=200)
    noise_steps: int | None = Field(default=None, ge=10, le=500)
    seed: int | None = None
    candidate_smiles: list[str] | None = None


class RunResponse(BaseModel):
    run_id: int
    status: str
    current_stage: str
    trace: list[dict]
    route: str | None = None
    state: dict | None = None


@router.post("/{project_id}/run", response_model=RunResponse)
async def start_run(
    project_id: int,
    body: RunRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.models.pipeline import PipelineRun
    from app.models.project import Project
    from app.orchestration.state import ACTIVE_STATUSES, REQUIRED_STAGES

    if body.route not in REQUIRED_STAGES:
        raise HTTPException(422, f"Unknown route {body.route!r}")
    if body.candidate_smiles is not None and not body.candidate_smiles:
        raise HTTPException(422, "candidate_smiles must be non-empty when provided")
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(404, "Project not found")
    active = (
        await session.execute(
            select(PipelineRun).where(
                PipelineRun.project_id == project_id,
                PipelineRun.status.in_(list(ACTIVE_STATUSES)),
            )
        )
    ).scalars().all()
    if active:
        raise HTTPException(409, "A pipeline run is already active for this project")
    # Regenerate/redock need a prior run to seed from; otherwise rerun retrieval.
    state = {
        "request_type": body.route,
        "project_id": project_id,
        "pdb_id": project.pdb_id,
        "seed_smiles": project.seed_smiles,
        "seed_name": None,
        "limit": 10,
        "gen_n": body.n or 20,
        "gen_noise_steps": body.noise_steps or 100,
        "gen_seed": body.seed,
        "candidate_smiles": body.candidate_smiles,
        "orchestrate": True,
        "status": "running",
        "trace": [],
    }
    if body.route in ("regenerate", "redock"):
        prior = (
            await session.execute(
                select(PipelineRun)
                .where(PipelineRun.project_id == project_id)
                .order_by(PipelineRun.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if prior and prior.state_json:
            prior_state = json.loads(prior.state_json)
            if prior_state.get("retrieve_results"):
                state["retrieve_results"] = prior_state["retrieve_results"]
                state["retrieve_done"] = True
                state["seed_resolved"] = prior_state.get("seed_resolved") or project.seed_smiles
            # Conditioning is what lets regenerate/both skip the retrieval
            # gate — copy it whenever the prior run recorded one.
            if prior_state.get("conditioning"):
                state["conditioning"] = prior_state["conditioning"]
            if prior_state.get("generate_results"):
                state["generate_results"] = prior_state["generate_results"]
                state["generate_done"] = True
    run = PipelineRun(
        project_id=project_id,
        route=body.route,
        status="running",
        current_stage="queued",
        state_json=json.dumps(state),
    )
    session.add(run)
    await session.flush()
    state["run_id"] = run.id
    await session.execute(
        select(PipelineRun).where(PipelineRun.id == run.id)
    )
    await session.commit()
    # Invoke the graph synchronously. In eager mode the generate/dock jobs
    # and their resume callbacks run inside this call and the row may already
    # be waiting (or done). The run row is the source of truth, not the
    # in-memory dict after the invoke.
    from app.orchestration.graph import graph, save_run

    _persist_inline(run.id, state)
    # LangGraph copies the input dict; adopt the returned state.
    state = graph.invoke(state)
    state["orchestrate"] = True
    state["run_id"] = run.id
    # Persist the traversed state (status/stage/trace) before returning.
    save_run(run.id, state, only_if_active=False)
    # Read the persisted row afresh from the database; using a fresh select
    # without expiring objects avoids MissingGreenlet on lazy-load.
    async with db.SessionLocal() as fresh_session:
        row = (
            await fresh_session.execute(
                select(PipelineRun).where(PipelineRun.id == run.id)
            )
        ).scalar_one()
        s = json.loads(row.state_json)
        return {
            "run_id": row.id,
            "status": row.status,
            "current_stage": row.current_stage or s.get("current_stage") or "done",
            "trace": s.get("trace") or [],
            "route": row.route,
            "state": s,
        }


@router.get("/{project_id}/run/{run_id}", response_model=RunResponse)
async def get_run(
    project_id: int,
    run_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.models.pipeline import PipelineRun

    row = (
        await session.execute(
            select(PipelineRun).where(
                PipelineRun.id == run_id, PipelineRun.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Run not found")
    state = json.loads(row.state_json)
    # Belt-and-braces: if the run is waiting, check whether its job already
    # completed (resume's .link_error may have been lost) and resume it here.
    if row.status == "waiting" and row.job_id:
        job_id = row.job_id
        try:
            from celery.result import AsyncResult

            from app.orchestration.graph import resume_run
            from app.workers.celery_app import celery

            r = AsyncResult(job_id, app=celery)
            if r.status == "SUCCESS":
                resume_run(run_id, {"failed": False, "result": r.result}, job_id)
                row = (
                    await session.execute(
                        select(PipelineRun).where(PipelineRun.id == run_id)
                    )
                ).scalar_one()
                state = json.loads(row.state_json)
            elif r.failed():
                resume_run(run_id, {"failed": True, "error": str(r.result)}, job_id)
                row = (
                    await session.execute(
                        select(PipelineRun).where(PipelineRun.id == run_id)
                    )
                ).scalar_one()
                state = json.loads(row.state_json)
        except Exception:
            pass
    return {
        "run_id": row.id,
        "status": row.status,
        "current_stage": row.current_stage or state.get("current_stage") or "done",
        "trace": state.get("trace") or [],
        "route": row.route,
        "state": state,
    }


def _persist_inline(run_id: int, state: dict) -> None:
    import asyncio

    from sqlalchemy import text

    from app import db

    async def _work() -> None:
        async with db.SessionLocal() as s:
            await s.execute(
                text(
                    "UPDATE pipeline_runs SET state_json=:s, status=:st, "
                    "current_stage=:cs, job_id=:j WHERE id=:id"
                ),
                {
                    "s": json.dumps(state),
                    "st": state.get("status") or "running",
                    "cs": state.get("current_stage") or "",
                    "j": state.get("generate_job_id") or state.get("dock_job_id"),
                    "id": run_id,
                },
            )
            await s.commit()

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_work())
        return
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, _work()).result()
