from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project,run_id_for
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import PerformanceAudit
router=APIRouter(tags=["Performance"])
def one(a):
    m=a.metrics_json or {}; return {"performance_score":a.performance_score,"accessibility_score":a.accessibility_score,"best_practices_score":a.best_practices_score,"seo_score":a.seo_score,"metrics":m,"core_web_vitals":m.get("core_web_vitals",{}),"lab_metrics":m.get("lab_metrics",{}),"field_data":m.get("field_data",{}),"opportunities":m.get("opportunities",[]),"metric_sources":m.get("metric_sources",{}),"status":a.status,"source":a.source,"warning":a.warning,"audit_id":a.id,"audited_at":a.audited_at.isoformat()}
@router.get("/projects/{project_id}/performance")
def performance(project_id:str,run_id:str|None=Query(None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rid=run_id_for(p,run_id); rows=list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==rid)))
    return {a.strategy.lower():one(a) for a in rows}
@router.get("/projects/{project_id}/performance/history")
def history(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rows=list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.project_id==p.id).order_by(PerformanceAudit.audited_at)))
    return [{"id":a.id,"runId":a.analysis_run_id,"strategy":a.strategy,"performance":a.performance_score,"metrics":a.metrics_json,"status":a.status,"date":a.audited_at.isoformat()} for a in rows]
@router.get("/projects/{project_id}/performance/compare")
def compare(project_id:str,from_:str=Query(alias="from"),to:str=Query(...),user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); a=db.get(PerformanceAudit,from_); b=db.get(PerformanceAudit,to)
    if not a or not b or a.project_id!=p.id or b.project_id!=p.id: raise AppError("PERFORMANCE_AUDIT_NOT_FOUND","One or both performance audits were not found.",404)
    fields=["performance_score","accessibility_score","best_practices_score","seo_score"]; diffs={}
    for f in fields:
        av=getattr(a,f); bv=getattr(b,f); diffs[f]={"from":av,"to":bv,"absolute":None if av is None or bv is None else round(bv-av,2),"percent":None if av in (None,0) or bv is None else round((bv-av)/av*100,2)}
    return {"from":a.id,"to":b.id,"differences":diffs}
