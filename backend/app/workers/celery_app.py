from celery import Celery
from app.core.config import settings
celery_app=Celery("hosting_advisor",broker=settings.celery_broker_url,backend=settings.celery_result_backend,include=["app.workers.analysis_tasks","app.workers.training_tasks"])
celery_app.conf.update(task_serializer="json",result_serializer="json",accept_content=["json"],task_track_started=True,worker_prefetch_multiplier=1,task_always_eager=settings.celery_task_always_eager,timezone="UTC",enable_utc=True)
celery_app.autodiscover_tasks(["app.workers"])
