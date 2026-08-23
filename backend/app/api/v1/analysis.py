import json,time
from fastapi import APIRouter,Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db,SessionLocal
from app.core.exceptions import AppError
from app.schemas.analysis import URLCheckRequest
from app.schemas.project import LiveFrontendRequest,PlannedFrontendRequest,IdeaFrontendRequest
from app.services.url_security_service import safe_fetch
from app.services.project_service import ProjectService
from app.services.analysis_pipeline import start_analysis,status_payload
from app.workers.analysis_tasks import enqueue_analysis
from app.models import AnalysisJob,Project
router=APIRouter(prefix="/analysis",tags=["Analysis"])
@router.post("/check-url")
@router.post("/check-website")
def check_url(req:URLCheckRequest,user=Depends(get_current_user)):
    r=safe_fetch(req.url,max_bytes=64_000); return {"reachable":200<=r["status_code"]<500,"status_code":r["status_code"],"normalized_url":r["url"],"response_time_ms":r["response_time_ms"]}
def _launch(db,user,mode,title,payload):
    p=ProjectService(db).create(user.id,mode,title,payload,"DRAFT"); j=start_analysis(db,p); enqueue_analysis(j.id); return {"id":p.id,"projectId":p.id,"jobId":j.id,"job_id":j.id,"status":"QUEUED","currency":"USD"}
@router.post("/live",status_code=202)
def start_live(req:LiveFrontendRequest,user=Depends(get_current_user),db:Session=Depends(get_db)): return _launch(db,user,"LIVE_URL",req.projectName,req.model_dump())
@router.post("/planned",status_code=202)
def start_planned(req:PlannedFrontendRequest,user=Depends(get_current_user),db:Session=Depends(get_db)): return _launch(db,user,"PLANNED",req.projectName,req.model_dump())
@router.post("/idea",status_code=202)
def start_idea(req:IdeaFrontendRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    data=req.model_dump(); title=req.projectName or (req.idea or req.description or "New Development Idea")[:100]; return _launch(db,user,"NEW_IDEA",title,data)
@router.get("/jobs/{job_id}")
def job_status(job_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    j=db.get(AnalysisJob,job_id)
    if not j: raise AppError("ANALYSIS_JOB_NOT_FOUND","Analysis job not found.",404)
    p=db.get(Project,j.project_id)
    if not p or p.user_id!=user.id: raise AppError("FORBIDDEN","You do not have access to this analysis job.",403)
    return status_payload(j)
@router.post("/jobs/{job_id}/cancel")
def cancel(job_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    j=db.get(AnalysisJob,job_id)
    if not j: raise AppError("ANALYSIS_JOB_NOT_FOUND","Analysis job not found.",404)
    p=db.get(Project,j.project_id)
    if p.user_id!=user.id: raise AppError("FORBIDDEN","You do not have access to this analysis job.",403)
    if j.status in {"COMPLETED","FAILED","CANCELLED"}: return status_payload(j)
    j.cancel_requested=True
    if j.status=="QUEUED": j.status="CANCELLED"; p.status="CANCELLED"
    db.commit(); return status_payload(j)
@router.get("/jobs/{job_id}/events")
def events(job_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    j=db.get(AnalysisJob,job_id)
    if not j: raise AppError("ANALYSIS_JOB_NOT_FOUND","Analysis job not found.",404)
    p=db.get(Project,j.project_id)
    if p.user_id!=user.id: raise AppError("FORBIDDEN","You do not have access to this analysis job.",403)
    uid=user.id
    def stream():
        last=None
        for _ in range(600):
            s=SessionLocal()
            try:
                row=s.get(AnalysisJob,job_id)
                if not row: break
                payload=status_payload(row); encoded=json.dumps(payload)
                if encoded!=last: yield f"event: progress\ndata: {encoded}\n\n"; last=encoded
                if row.status in {"COMPLETED","FAILED","CANCELLED"}: break
            finally:s.close()
            time.sleep(2)
    return StreamingResponse(stream(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
