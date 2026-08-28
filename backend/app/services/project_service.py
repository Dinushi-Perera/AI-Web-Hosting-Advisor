from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Project, ProjectInput, PerformanceAudit, Recommendation, AuditLog
from app.core.exceptions import AppError

def mode_internal(mode:str):
    m=mode.upper().replace("-","_")
    return {"LIVE":"LIVE_URL","IDEA":"NEW_IDEA","LIVE_URL":"LIVE_URL","PLANNED":"PLANNED","NEW_IDEA":"NEW_IDEA"}.get(m,m)
def mode_front(m:str): return {"LIVE_URL":"LIVE","NEW_IDEA":"IDEA"}.get(m,m)
def status_front(s:str): return {"DRAFT":"Draft","QUEUED":"Queued","ANALYSING":"Analysing","COMPLETED":"Completed","NEEDS_ATTENTION":"Needs Attention","FAILED":"Failed","CANCELLED":"Cancelled","ARCHIVED":"Archived"}.get(s,s.title())

def completeness(payload:dict)->float:
    if not payload: return 0.0
    meaningful=[v for v in payload.values() if v not in (None,"",[],{},"Unknown","Not Decided","Unsure")]
    return round(min(1.0,len(meaningful)/max(8,len(payload))),2)

def normalized_payload(payload:dict)->dict:
    """Remove retired client preferences and keep the monetary unit server-owned."""
    blocked={"region","target_region","targetRegion","defaultRegion","currency","defaultCurrency"}
    return {**{k:v for k,v in payload.items() if k not in blocked},"currency":"USD"}

class ProjectService:
    def __init__(self,db:Session): self.db=db
    def create(self,user_id:str,mode:str,title:str,payload:dict,status="DRAFT"):
        currency=str(payload.get("currency","USD")).upper()
        if currency!="USD": raise AppError("CURRENCY_UNSUPPORTED","Only USD is supported.",422)
        payload=normalized_payload(payload)
        website=payload.get("websiteUrl") or payload.get("url")
        p=Project(user_id=user_id,title=title.strip(),mode=mode_internal(mode),status=status,website_url=website,currency="USD")
        self.db.add(p); self.db.flush(); self.db.add(ProjectInput(project_id=p.id,payload={**payload,"currency":"USD"},completeness_score=completeness(payload))); self.db.add(AuditLog(actor_user_id=user_id,action="PROJECT_CREATED",entity_type="PROJECT",entity_id=p.id)); self.db.commit(); return p
    def owned(self,project_id,user):
        p=self.db.get(Project,project_id)
        if not p or p.deleted_at is not None: raise AppError("PROJECT_NOT_FOUND","Project not found.",404)
        if p.user_id!=user.id: raise AppError("FORBIDDEN","You do not have access to this project.",403)
        return p
    def update(self,p,user,patch:dict):
        if "currency" in patch and patch["currency"] and str(patch["currency"]).upper()!="USD": raise AppError("CURRENCY_UNSUPPORTED","Only USD is supported.",422)
        if patch.get("title") or patch.get("name"): p.title=patch.get("title") or patch.get("name")
        if patch.get("status"): p.status=str(patch["status"]).upper().replace(" ","_")
        inp=self.db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id))
        incoming=patch.get("input") or {k:v for k,v in patch.items() if k not in {"title","name","status"} and v is not None}
        if incoming:
            merged=normalized_payload({**(inp.payload if inp else {}),**incoming})
            if inp: inp.payload=merged; inp.completeness_score=completeness(merged)
            else: self.db.add(ProjectInput(project_id=p.id,payload=merged,completeness_score=completeness(merged)))
            p.recommendation_stale=True
        self.db.add(AuditLog(actor_user_id=user.id,action="INPUT_UPDATED",entity_type="PROJECT",entity_id=p.id)); self.db.commit(); return p
    def serialize(self,p:Project):
        perf=None; rec=None
        if p.latest_analysis_run_id:
            perf=self.db.scalar(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==p.latest_analysis_run_id,PerformanceAudit.strategy=="MOBILE"))
            rec=self.db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==p.latest_analysis_run_id))
        cost_min=rec.estimated_cost.get("min") if rec and rec.estimated_cost else None
        cost_max=rec.estimated_cost.get("max") if rec and rec.estimated_cost else None
        cost_range=[cost_min,cost_max] if cost_min is not None and cost_max is not None else None
        return {"id":p.id,"name":p.title,"mode":mode_front(p.mode),"website":p.website_url,"status":status_front(p.status),"performanceScore":round(perf.performance_score) if perf and perf.performance_score is not None else None,"recommendation":{"VPS":"VPS","CLOUD_VM":"Cloud VM","KUBERNETES":"Kubernetes"}.get(rec.recommended_option) if rec else None,"costRange":cost_range,"confidence":round(rec.confidence_value*100) if rec else None,"currency":"USD","updatedAt":p.updated_at.isoformat()}
