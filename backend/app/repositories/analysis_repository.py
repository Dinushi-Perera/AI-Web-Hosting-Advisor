from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import AnalysisRun, AnalysisJob
class AnalysisRepository:
    def __init__(self,db:Session): self.db=db
    def active_job(self,project_id:str): return self.db.scalar(select(AnalysisJob).where(AnalysisJob.project_id==project_id,AnalysisJob.status.in_(["QUEUED","RUNNING"])).order_by(AnalysisJob.created_at.desc()))
    def run(self,run_id:str): return self.db.get(AnalysisRun,run_id)
    def job(self,job_id:str): return self.db.get(AnalysisJob,job_id)
