from datetime import datetime, timezone
from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import Project,ProjectInput,AuditLog,AnalysisJob,AnalysisRun,TechnologyDetection,PerformanceAudit,WorkloadEstimate,Recommendation,Optimization,LoadTestPlan,LoadTestResult,Report,Feedback,Notification,TestResult
from app.schemas.project import ProjectCreate,ProjectPatch
from app.services.project_service import ProjectService,mode_internal,normalized_payload
from app.services.analysis_pipeline import start_analysis
from app.workers.analysis_tasks import enqueue_analysis
from app.services.project_validation_service import evaluate_project
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
    extra=getattr(req,"__pydantic_extra__",{}) or {}; payload=req.input or extra; title=req.title or req.name or req.projectName or "Untitled Project"; p=ProjectService(db).create(user.id,req.mode,title,payload,req.status.upper()); return ProjectService(db).serialize(p)
@router.get("/{project_id}")
def get_project(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user); out=ProjectService(db).serialize(p); inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id)); out["input"]=normalized_payload(inp.payload) if inp else {"currency":"USD"}; out["latestAnalysisRunId"]=p.latest_analysis_run_id; out["recommendationStale"]=p.recommendation_stale; return out
@router.get("/{project_id}/analysis-summary")
def analysis_summary(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=ProjectService(db).owned(project_id,user);rid=p.latest_analysis_run_id;inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id));payload=normalized_payload(inp.payload) if inp else {"currency":"USD"}
    tech=list(db.scalars(select(TechnologyDetection).where(TechnologyDetection.analysis_run_id==rid))) if rid else []
    perf=list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==rid))) if rid else []
    workload=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==rid)) if rid else None
    rec=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==rid)) if rid else None
    opts=list(db.scalars(select(Optimization).where(Optimization.analysis_run_id==rid))) if rid else []
    plans=list(db.scalars(select(LoadTestPlan).where(LoadTestPlan.project_id==p.id)))
    results=list(db.scalars(select(LoadTestResult).where(LoadTestResult.project_id==p.id)))
    reports=list(db.scalars(select(Report).where(Report.project_id==p.id,Report.deleted_at.is_(None))))
    feedback=list(db.scalars(select(Feedback).where(Feedback.project_id==p.id)))
    events=list(db.scalars(select(AuditLog).where(AuditLog.entity_type=="PROJECT",AuditLog.entity_id==p.id).order_by(AuditLog.created_at.desc())))
    notices=list(db.scalars(select(Notification).where(Notification.user_id==user.id)))
    notices=[n for n in notices if (n.data or {}).get("project_id")==p.id]
    tests=[row for row in db.scalars(select(TestResult).order_by(TestResult.executed_at.desc()).limit(250)) if not (row.details or {}).get("project_id") or (row.details or {}).get("project_id")==p.id]
    latest_job=db.scalar(select(AnalysisJob).where(AnalysisJob.project_id==p.id).order_by(AnalysisJob.created_at.desc()))
    performance_available=any(a.performance_score is not None for a in perf);performance_planned=bool(perf) and not performance_available
    budget=payload.get("budget") or payload.get("monthly_budget")
    try:budget_value=float(budget) if budget not in (None,"") else None
    except (TypeError,ValueError):budget_value=None
    cost=rec.estimated_cost if rec else {};cost_min=cost.get("min") if cost else None;cost_max=cost.get("max") if cost else None
    coverage=[
        {"section":"Input","complete":bool(payload),"count":len([v for v in payload.values() if v not in (None,"",[],{})]),"note":f"{round((inp.completeness_score if inp else 0)*100)}% completeness"},
        {"section":"Technology","complete":bool(tech) or p.mode!="LIVE_URL","count":len(tech),"note":"Detected evidence" if p.mode=="LIVE_URL" else "Declared or suggested stack"},
        {"section":"Performance","complete":bool(perf),"count":len(perf),"note":"Measured audit" if performance_available else "Pre-launch budget" if performance_planned else "Unavailable"},
        {"section":"Workload","complete":workload is not None,"count":1 if workload else 0,"note":workload.classification if workload else "Pending"},
        {"section":"Recommendation","complete":rec is not None,"count":1 if rec else 0,"note":rec.recommended_option if rec else "Pending"},
        {"section":"Optimization","complete":bool(opts),"count":len(opts),"note":f"{sum(1 for x in opts if x.status=='OPEN')} open actions"},
        {"section":"Load Test","complete":bool(plans),"count":len(results),"note":f"{len(plans)} plans / {len(results)} results"},
        {"section":"Report","complete":bool(reports),"count":len(reports),"note":f"{len(reports)} versions"},
    ]
    concurrent=workload.concurrent_users if workload else payload.get("concurrentUsers");peak=workload.peak_rps if workload else None
    factors=[
        {"factor":"Traffic","score":min(100,round((peak or 0)/5)),"value":f"{concurrent or 'Unknown'} concurrent / {peak or 'Unknown'} peak RPS","effect":"Higher concurrency and peak requests increase CPU, memory and scaling needs."},
        {"factor":"Budget Fit","score":0 if budget_value is None or cost_max is None else 100 if cost_max<=budget_value else 60 if cost_min is not None and cost_min<=budget_value else 20,"value":f"USD {budget or 'Unknown'} budget vs {cost_min if cost_min is not None else '?'}-{cost_max if cost_max is not None else '?'} estimate","effect":"The budget limits options that would be financially unsustainable."},
        {"factor":"Evidence","score":round((rec.confidence_value if rec else 0)*100),"value":rec.confidence_label if rec else "Pending","effect":"Measured and complete inputs raise confidence; assumptions reduce it."},
        {"factor":"Performance","score":round(sum(a.performance_score for a in perf if a.performance_score is not None)/len([a for a in perf if a.performance_score is not None])) if performance_available else 50 if performance_planned else 20,"value":"Measured" if performance_available else "Planned target" if performance_planned else "Unavailable","effect":"Poor measured performance triggers optimization before unnecessary server upgrades."},
        {"factor":"Operations","score":85 if payload.get("kubernetesSkill") or str(payload.get("experience","")).lower()=="advanced" else 55 if payload.get("managesServers") or str(payload.get("experience","")).lower()=="intermediate" else 30,"value":str(payload.get("experience") or ("Server management" if payload.get("managesServers") else "Limited operations input")),"effect":"Operational skill constrains architectures that would be difficult to run safely."},
    ]
    test_counts={name:{"passed":0,"failed":0,"notRun":0,"total":0} for name in ("UT","IT","ST","UAT","ORT")}
    aliases={"UNIT":"UT","INTEGRATION":"IT","SYSTEM":"ST"}
    for row in tests:
        key=aliases.get(row.test_type,row.test_type)
        if key not in test_counts:continue
        test_counts[key]["total"]+=1;bucket="passed" if row.status.upper()=="PASSED" else "notRun" if row.status.upper() in {"SKIPPED","NOT_RUN","WARNING"} else "failed";test_counts[key][bucket]+=1
    project_tests=evaluate_project(db,p,rid) if rid and rec else []
    return {"project":{"id":p.id,"title":p.title,"mode":p.mode,"status":p.status,"website":p.website_url},"input":payload,"coverage":coverage,"decisionFactors":factors,"model":{"version":rec.model_version if rec else None,"probabilities":rec.model_probabilities if rec else {},"resourceSize":rec.resource_size if rec else {},"recommended":rec.recommended_option if rec else None,"confidence":rec.confidence_value if rec else None,"decisionEvidence":rec.decision_evidence if rec else {},"costOptimization":rec.cost_optimization if rec else {},"llmExplanation":rec.llm_explanation if rec else {},"llmStatus":rec.llm_status if rec else None},"testing":test_counts,"projectTests":project_tests,"activity":{"events":len(events),"notifications":len(notices),"reports":len(reports),"feedback":len(feedback),"loadTestPlans":len(plans),"loadTestResults":len(results)},"progress":{"status":latest_job.status,"progress":latest_job.progress,"currentStage":latest_job.current_stage,"stages":latest_job.stages_json} if latest_job else None}
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
    p=ProjectService(db).owned(project_id,user); p.status="ARCHIVED"; p.archived_at=datetime.now(timezone.utc);db.add(AuditLog(actor_user_id=user.id,action="PROJECT_ARCHIVED",entity_type="PROJECT",entity_id=p.id));db.commit(); return ProjectService(db).serialize(p)
@router.post("/{project_id}/restore")
def restore(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p or p.user_id!=user.id: raise AppError("PROJECT_NOT_FOUND","Project not found.",404)
    p.status="DRAFT"; p.archived_at=None; p.deleted_at=None;db.add(AuditLog(actor_user_id=user.id,action="PROJECT_RESTORED",entity_type="PROJECT",entity_id=p.id));db.commit(); return ProjectService(db).serialize(p)
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
