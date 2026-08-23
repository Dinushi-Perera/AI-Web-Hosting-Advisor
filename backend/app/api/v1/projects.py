from datetime import datetime, timezone
from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import Project,ProjectInput,AuditLog,AnalysisJob,AnalysisRun
from app.schemas.project import ProjectCreate,ProjectPatch
from app.services.project_service import ProjectService,mode_internal
from app.services.analysis_pipeline import start_analysis
from app.workers.analysis_tasks import enqueue_analysis
router=APIRouter(prefix="/projects",tags=["Projects"])
@router.get("")
def list_projects(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),mode:str|None=None,status:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    q=select(Project).where(Project.user_id==user.id,Project.deleted_at.is_(None))
    if mode:q=q.where(Project.mode==mode_internal(mode))
    if status:q=q.where(Project.status==status.upper().replace(" ","_"))
    rows=list(db.scalars(q.order_by(Project.updated_at.desc()).offset((page-1)*page_size).limit(page_size)))
    return [ProjectService(db).serialize(p) for p in rows]
@router.post("",status_code=201)
def create_project(req:ProjectCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    d=req.model_dump(exclude_none=True); extra=getattr(req,"__pydantic_extra__",{}) or {}; payload=req.input or {**extra,"currency":req.currency}; title=req.title or req.name or req.projectName or "Untitled Project"; p=ProjectService(db).create(user.id,req.mode,title,payload,req.status.upper()); return ProjectService(db).serialize(p)
@router.get("/{project_id}")
def get_project(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); out=ProjectService(db).serialize(p); inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id)); out["input"]=inp.payload if inp else {}; out["latestAnalysisRunId"]=p.latest_analysis_run_id; out["recommendationStale"]=p.recommendation_stale; return out
@router.patch("/{project_id}")
def update_project(project_id:str,req:ProjectPatch,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); d=req.model_dump(exclude_none=True); d.update(getattr(req,"__pydantic_extra__",{}) or {}); ProjectService(db).update(p,user,d); return ProjectService(db).serialize(p)
@router.delete("/{project_id}")
def delete_project(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); p.deleted_at=datetime.now(timezone.utc); db.add(AuditLog(actor_user_id=user.id,action="PROJECT_DELETE",entity_type="PROJECT",entity_id=p.id)); db.commit(); return {"success":True}
@router.post("/{project_id}/duplicate",status_code=201)
def duplicate(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id)); cp=ProjectService(db).create(user.id,p.mode,f"{p.title} Copy",dict(inp.payload if inp else {}),"DRAFT"); return ProjectService(db).serialize(cp)
@router.post("/{project_id}/archive")
def archive(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); p.status="ARCHIVED"; p.archived_at=datetime.now(timezone.utc); db.commit(); return ProjectService(db).serialize(p)
@router.post("/{project_id}/restore")
def restore(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p or p.user_id!=user.id: raise AppError("PROJECT_NOT_FOUND","Project not found.",404)
    p.status="DRAFT"; p.archived_at=None; p.deleted_at=None; db.commit(); return ProjectService(db).serialize(p)
@router.post("/{project_id}/validate")
def validate_project(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id)); payload=inp.payload if inp else {}; missing=[]
    required=[("projectName","Project name is required.")]
    if p.mode=="LIVE_URL": required += [("websiteUrl","Website URL is required."),("concurrentUsers","Peak concurrent users are required.")]
    for k,msg in required:
        if k=="projectName": val=p.title
        else: val=payload.get(k)
        if val in (None,""): missing.append({"field":k,"message":msg})
    return {"valid":not missing,"missing_fields":missing}
@router.patch("/{project_id}/inputs")
def update_inputs(project_id:str,payload:dict,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); ProjectService(db).update(p,user,{"input":payload}); return {"success":True,"projectId":p.id}
@router.post("/{project_id}/analysis",status_code=202)
def analyse(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); j=start_analysis(db,p); enqueue_analysis(j.id); return {"job_id":j.id,"jobId":j.id,"project_id":p.id,"projectId":p.id,"status":"QUEUED"}
@router.get("/{project_id}/history")
def history(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); runs=list(db.scalars(select(AnalysisRun).where(AnalysisRun.project_id==p.id).order_by(AnalysisRun.created_at.desc())))
    logs=list(db.scalars(select(AuditLog).where(AuditLog.entity_type=="PROJECT",AuditLog.entity_id==p.id).order_by(AuditLog.created_at.desc())))
    return {"runs":[{"id":r.id,"jobId":r.job_id,"status":r.status,"startedAt":r.started_at.isoformat() if r.started_at else None,"completedAt":r.completed_at.isoformat() if r.completed_at else None} for r in runs],"events":[{"action":x.action,"timestamp":x.created_at.isoformat(),"actor":"You" if x.actor_user_id==user.id else "System","metadata":x.metadata_json} for x in logs]}

@router.post("/drafts",status_code=201)
def create_draft(payload:dict,user=Depends(get_current_user),db:Session=Depends(get_db)):
    mode=payload.get("mode","PLANNED"); title=payload.get("title") or payload.get("projectName") or "Untitled Draft"; data=payload.get("input") or payload; data["currency"]="USD"; p=ProjectService(db).create(user.id,mode,title,data,"DRAFT"); return ProjectService(db).serialize(p)

@router.patch("/{project_id}/draft")
def patch_draft(project_id:str,payload:dict,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); p.status="DRAFT"; ProjectService(db).update(p,user,{"input":payload,"status":"DRAFT"}); return ProjectService(db).serialize(p)
