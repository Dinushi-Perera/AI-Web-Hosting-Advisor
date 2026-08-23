from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Report
class ReportRepository:
    def __init__(self,db:Session): self.db=db
    def owned(self,report_id:str,user_id:str):
        r=self.db.get(Report,report_id); return r if r and r.deleted_at is None and r.user_id==user_id else None
    def for_project(self,project_id:str): return list(self.db.scalars(select(Report).where(Report.project_id==project_id,Report.deleted_at.is_(None)).order_by(Report.generated_at.desc())))
