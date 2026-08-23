from datetime import datetime,timezone
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import ModelTrainingJob,MLModelVersion
from app.ml.trainer import train
@celery_app.task(name="app.workers.training_tasks.train_model_task",bind=True)
def train_model_task(self,job_id:str):
    db=SessionLocal(); job=db.get(ModelTrainingJob,job_id)
    try:
        job.status="RUNNING"; job.current_stage="VALIDATING"; job.progress=10; db.commit()
        job.current_stage="TRAINING"; job.progress=40; db.commit(); result=train(job.dataset_path)
        job.current_stage="SAVING"; job.progress=85; db.commit(); model=MLModelVersion(**result,is_active=False); db.add(model); db.flush(); job.result_model_id=model.id; job.status="COMPLETED"; job.current_stage="COMPLETED"; job.progress=100; job.completed_at=datetime.now(timezone.utc); db.commit(); return {"job_id":job.id,"model_id":model.id}
    except Exception:
        if job: job.status="FAILED"; job.current_stage="FAILED"; job.error_message="Model training failed. Review dataset validation and worker logs."; job.completed_at=datetime.now(timezone.utc); db.commit()
        raise
    finally: db.close()
def enqueue_training(job_id:str):
    if celery_app.conf.task_always_eager:return train_model_task.apply(args=[job_id])
    try:
        return train_model_task.delay(job_id)
    except Exception as exc:
        from app.core.exceptions import AppError
        raise AppError("SERVICE_UNAVAILABLE","Background model-training queue is unavailable.",503) from exc
