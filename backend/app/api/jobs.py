from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workers import tasks
from app.workers.celery_app import celery

router = APIRouter()


class TestJobRequest(BaseModel):
    a: int = 1
    b: int = 2


@router.post("/test")
def enqueue_test_job(body: TestJobRequest) -> dict:
    result = tasks.add.delay(body.a, body.b)
    return {"id": result.id, "status": "queued"}


class GenerateRequest(BaseModel):
    n: int = Field(default=10, ge=1, le=200)
    mw_min: float | None = None
    mw_max: float | None = None
    logp_min: float | None = None
    logp_max: float | None = None
    seed: int | None = None
    seed_smiles: str | None = None
    noise_steps: int = Field(default=100, ge=10, le=500)


@router.post("/generate")
def enqueue_generate(body: GenerateRequest) -> dict:
    mw_range = (body.mw_min, body.mw_max) if body.mw_min or body.mw_max else None
    logp_range = (body.logp_min, body.logp_max) if body.logp_min or body.logp_max else None
    for name, r in (("mw_range", mw_range), ("logp_range", logp_range)):
        if r and r[0] is not None and r[1] is not None and r[0] > r[1]:
            raise HTTPException(422, f"{name}: min exceeds max")
    if body.seed_smiles:
        from app.chem.embeddings import parse_smiles

        if parse_smiles(body.seed_smiles) is None:
            raise HTTPException(422, "Invalid seed_smiles")
    result = tasks.generate_molecules.delay(
        body.n, mw_range, logp_range, body.seed, body.seed_smiles, body.noise_steps
    )
    return {"id": result.id, "status": "queued"}


@router.get("/{job_id}")
def get_job(job_id: str) -> dict:
    result = AsyncResult(job_id, app=celery)
    payload: dict = {"id": job_id, "status": result.status.lower()}
    if result.status == "SUCCESS":
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = str(result.result)
    return payload
