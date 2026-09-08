from app.workers.celery_app import celery


@celery.task(name="add")
def add(a: int, b: int) -> int:
    return a + b
