from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Project,ProjectInput
from app.services.project_service import ProjectService
from app.core.exceptions import AppError
def owned_project(db:Session,project_id:str,user): return ProjectService(db).owned(project_id,user)
def run_id_for(project:Project,run_id:str|None=None):
    rid=run_id or project.latest_analysis_run_id
    if not rid: raise AppError("ANALYSIS_NOT_FOUND","No analysis is available for this project.",404)
    return rid
def project_payload(db:Session,project_id:str):
    row=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project_id)); return row.payload if row else {}
