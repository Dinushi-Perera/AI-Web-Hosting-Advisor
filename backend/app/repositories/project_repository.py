from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Project, ProjectInput
class ProjectRepository:
    def __init__(self,db:Session): self.db=db
    def owned(self,project_id:str,user_id:str):
        p=self.db.get(Project,project_id)
        return p if p and p.deleted_at is None and p.user_id==user_id else None
    def list_owned(self,user_id:str):
        return list(self.db.scalars(select(Project).where(Project.user_id==user_id,Project.deleted_at.is_(None)).order_by(Project.updated_at.desc())))
    def input_for(self,project_id:str): return self.db.scalar(select(ProjectInput).where(ProjectInput.project_id==project_id))
