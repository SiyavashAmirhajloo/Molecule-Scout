from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

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


@router.get("/{job_id}")
def get_job(job_id: str) -> dict:
    result = AsyncResult(job_id, app=celery)
    payload: dict = {"id": job_id, "status": result.status.lower()}
    if result.status == "SUCCESS":
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = str(result.result)
    return payload
