from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.analysis_pipeline import process_analysis
@celery_app.task(name="app.workers.analysis_tasks.process_analysis_task",bind=True,acks_late=True)
def process_analysis_task(self,job_id:str):
    db=SessionLocal()
    try:
        job=db.get(__import__('app.models',fromlist=['AnalysisJob']).AnalysisJob,job_id)
        if job: job.worker_id=self.request.id; db.commit()
        result=process_analysis(db,job_id); return {"job_id":result.id,"status":result.status}
    finally: db.close()
def enqueue_analysis(job_id:str):
    if celery_app.conf.task_always_eager:
        return process_analysis_task.apply(args=[job_id])
    try:
        return process_analysis_task.delay(job_id)
    except Exception as exc:
        from datetime import datetime, timezone
        from app.models import AnalysisJob, AnalysisRun, Project
        from app.core.exceptions import AppError
        db=SessionLocal()
        try:
            job=db.get(AnalysisJob,job_id)
            if job:
                job.status="FAILED"; job.error_code="QUEUE_UNAVAILABLE"; job.error_message="Background analysis queue is unavailable."; job.completed_at=datetime.now(timezone.utc)
                run=db.get(AnalysisRun,job.analysis_run_id); project=db.get(Project,job.project_id)
                if run: run.status="FAILED"; run.completed_at=datetime.now(timezone.utc)
                if project: project.status="FAILED"
                db.commit()
        finally: db.close()
        raise AppError("SERVICE_UNAVAILABLE","Background analysis queue is unavailable.",503) from exc

@celery_app.task(name="app.workers.analysis_tasks.sweep_stale_analysis_jobs")
def sweep_stale_analysis_jobs(max_age_minutes:int=60):
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.models import AnalysisJob, AnalysisRun, Project
    db=SessionLocal(); cutoff=datetime.now(timezone.utc)-timedelta(minutes=max_age_minutes); count=0
    try:
        rows=list(db.scalars(select(AnalysisJob).where(AnalysisJob.status=="RUNNING",AnalysisJob.started_at < cutoff)))
        for job in rows:
            job.status="FAILED";job.error_code="WORKER_TIMEOUT";job.error_message="Analysis worker stopped before completion.";job.completed_at=datetime.now(timezone.utc)
            run=db.get(AnalysisRun,job.analysis_run_id);project=db.get(Project,job.project_id)
            if run:run.status="FAILED";run.completed_at=datetime.now(timezone.utc)
            if project:project.status="FAILED"
            count+=1
        db.commit();return {"failed_stale_jobs":count}
    finally:db.close()
