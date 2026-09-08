from fastapi.testclient import TestClient

from app.main import create_app
from app.workers.celery_app import celery

celery.conf.update(
    task_always_eager=True,
    task_store_eager_result=True,
    result_backend="cache+memory://",
)


def test_enqueue_and_poll_eager():
    with TestClient(create_app()) as client:
        enqueued = client.post("/jobs/test", json={"a": 1, "b": 2})
        assert enqueued.status_code == 200
        job_id = enqueued.json()["id"]
        polled = client.get(f"/jobs/{job_id}")
    assert polled.status_code == 200
    assert polled.json()["status"] == "success"
    assert polled.json()["result"] == 3
