from pathlib import Path
from datetime import datetime,timezone
from fastapi import APIRouter,Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import Report
from app.services.report_service import generate_report
router=APIRouter(tags=["Reports"])
def rj(r):
    project=(r.snapshot or {}).get("project",{}); recommendation=(r.snapshot or {}).get("recommendation",{})
    return {"id":r.id,"projectId":r.project_id,"projectTitle":project.get("title","Project Report"),"projectMode":project.get("mode"),"recommendation":recommendation.get("recommended_option"),"analysisRunId":r.analysis_run_id,"version":r.version,"generatedAt":r.generated_at.isoformat(),"status":r.status,"currency":"USD"}
@router.get("/reports")
def all_reports(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return [rj(r) for r in db.scalars(select(Report).where(Report.user_id==user.id,Report.deleted_at.is_(None)).order_by(Report.generated_at.desc()))]
@router.post("/projects/{project_id}/reports",status_code=201)
def generate(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return rj(generate_report(db,p,user.id))
@router.get("/projects/{project_id}/reports")
def project_reports(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return [rj(r) for r in db.scalars(select(Report).where(Report.project_id==p.id,Report.deleted_at.is_(None)).order_by(Report.generated_at.desc()))]
@router.get("/reports/{report_id}")
def get_report(report_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(Report,report_id)
    if not r or r.deleted_at or r.user_id!=user.id: raise AppError("REPORT_NOT_FOUND","Report not found.",404)
    return {**rj(r),"snapshot":r.snapshot}
@router.get("/reports/{report_id}/pdf")
def pdf(report_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(Report,report_id)
    if not r or r.deleted_at or r.user_id!=user.id: raise AppError("REPORT_NOT_FOUND","Report not found.",404)
    path=Path(settings.report_storage_dir)/Path(r.file_key or "").name
    if not path.exists(): raise AppError("FILE_NOT_FOUND","Report PDF is unavailable.",404)
    return FileResponse(path,media_type="application/pdf",filename=f"hosting-advisor-report-v{r.version}.pdf")
@router.post("/reports/{report_id}/regenerate",status_code=201)
def regenerate(report_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(Report,report_id)
    if not r or r.deleted_at or r.user_id!=user.id: raise AppError("REPORT_NOT_FOUND","Report not found.",404)
    p=owned_project(db,r.project_id,user); return rj(generate_report(db,p,user.id))
@router.delete("/reports/{report_id}")
def delete_report(report_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(Report,report_id)
    if not r or r.deleted_at or r.user_id!=user.id: raise AppError("REPORT_NOT_FOUND","Report not found.",404)
    path=Path(settings.report_storage_dir)/Path(r.file_key or "").name
    if path.exists(): path.unlink()
    r.deleted_at=datetime.now(timezone.utc); db.commit(); return {"success":True}
