from celery import Celery

from app.config import settings

celery = Celery("moleculescout", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(task_track_started=True)
celery.autodiscover_tasks(["app.workers"])
