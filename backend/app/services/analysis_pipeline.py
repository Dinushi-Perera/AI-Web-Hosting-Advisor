from datetime import datetime, timezone
import logging
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models import Project, ProjectInput, AnalysisRun, AnalysisJob, TechnologyDetection, TechnologyEvidence, PerformanceAudit, WorkloadEstimate, Recommendation, RecommendationScore, Optimization, ModelPrediction, AuditLog
from app.services.url_security_service import validate_public_url, safe_fetch
from app.services.technology_detector import detect_from_response
from app.services.performance_service import audit as performance_audit
from app.services.workload_estimator import estimate as estimate_workload
from app.services.recommendation_service import build as build_recommendation, technology_suggestion
from app.services.optimization_service import generate as generate_optimizations
from app.services.notification_service import create_notification
from app.services.report_service import generate_report
from app.core.exceptions import AppError
from app.utils.enums import AnalysisStage

logger = logging.getLogger(__name__)

def utcnow(): return datetime.now(timezone.utc)
ALL_STAGES=[s.value for s in AnalysisStage]

def _job(db,job_id):
    j=db.get(AnalysisJob,job_id)
    if not j: raise AppError("ANALYSIS_JOB_NOT_FOUND","Analysis job not found.",404)
    return j

def set_stage(db:Session,j:AnalysisJob,stage:str,index:int):
    if j.cancel_requested:
        j.status="CANCELLED"; j.completed_at=utcnow(); db.commit(); raise AppError("ANALYSIS_CANCELLED","Analysis was cancelled.",409)
    stages=[]
    for i,name in enumerate(ALL_STAGES): stages.append({"name":name,"status":"COMPLETED" if i<index else "RUNNING" if i==index else "PENDING"})
    j.current_stage=stage; j.progress=round(index/max(1,len(ALL_STAGES))*100); j.stages_json=stages; db.commit()

def start_analysis(db:Session,project:Project)->AnalysisJob:
    active=db.scalar(select(AnalysisJob).where(AnalysisJob.project_id==project.id,AnalysisJob.status.in_(["QUEUED","RUNNING"])).order_by(AnalysisJob.created_at.desc()))
    if active: raise AppError("ANALYSIS_ALREADY_RUNNING","An analysis is already running for this project.",409,{"job_id":active.id})
    inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project.id))
    if not inp: raise AppError("VALIDATION_ERROR","Project input is missing.",422)
    payload=inp.payload or {}
    if project.mode=="LIVE_URL" and not (payload.get("websiteUrl") or project.website_url): raise AppError("VALIDATION_ERROR","Website URL is required.",422,{"missing_fields":["websiteUrl"]})
    run=AnalysisRun(project_id=project.id,status="QUEUED"); db.add(run); db.flush()
    stages=[{"name":x,"status":"PENDING"} for x in ALL_STAGES]
    j=AnalysisJob(project_id=project.id,analysis_run_id=run.id,status="QUEUED",progress=0,stages_json=stages); db.add(j); db.flush(); run.job_id=j.id; project.latest_analysis_run_id=run.id; project.status="QUEUED"; project.recommendation_stale=False
    db.add(AuditLog(actor_user_id=project.user_id,action="ANALYSIS_STARTED",entity_type="PROJECT",entity_id=project.id,metadata_json={"job_id":j.id,"run_id":run.id})); db.commit(); return j

def process_analysis(db:Session,job_id:str):
    j=_job(db,job_id); p=db.get(Project,j.project_id); run=db.get(AnalysisRun,j.analysis_run_id); inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==p.id)); payload=inp.payload or {}
    j.status="RUNNING"; j.started_at=utcnow(); run.status="RUNNING"; run.started_at=utcnow(); p.status="ANALYSING"; db.commit()
    tech=[]; perf=[]
    try:
        set_stage(db,j,"URL_VALIDATION",0)
        response=None
        if p.mode=="LIVE_URL":
            url=validate_public_url(payload.get("websiteUrl") or p.website_url); response=safe_fetch(url); p.website_url=url
        set_stage(db,j,"TECHNOLOGY_DETECTION",1)
        if p.mode=="LIVE_URL" and response:
            tech=detect_from_response(response)
        elif p.mode=="NEW_IDEA":
            sugg=technology_suggestion(payload); tech=[{"category":cat.upper(),"technology":x["technology"],"confidence":x["score"]/100,"confidence_label":"HIGH" if x["score"]>=80 else "MEDIUM","evidence":[{"source":"DECLARED_IDEA","pattern":x["reason"],"weight":x["score"]/100}]} for cat,items in sugg.items() if isinstance(items,list) for x in items]
        else:
            pairs=[("FRONTEND",payload.get("frontend")),("BACKEND",payload.get("backend")),("DATABASE",payload.get("database")),("CMS",payload.get("cms")),("CACHE",payload.get("cache")),("CDN",payload.get("cdn"))]
            tech=[{"category":c,"technology":v,"confidence":0.98,"confidence_label":"HIGH","evidence":[{"source":"USER_DECLARED","pattern":"Declared in project input","weight":0.98}]} for c,v in pairs if v and v not in {"Not Decided","None"}]
        for t in tech:
            td=TechnologyDetection(project_id=p.id,analysis_run_id=run.id,technology=t["technology"],category=t["category"],confidence=t["confidence"],confidence_label=t["confidence_label"]); db.add(td); db.flush()
            for e in t.get("evidence",[]): db.add(TechnologyEvidence(detection_id=td.id,source=e.get("source","UNKNOWN"),pattern=str(e.get("pattern",""))[:255],value_masked=None,weight=float(e.get("weight",1))))
        db.commit()
        set_stage(db,j,"PERFORMANCE_AUDIT",2)
        perf=performance_audit(p.website_url) if p.mode=="LIVE_URL" and p.website_url else [{"strategy":"MOBILE","status":"UNAVAILABLE","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":{},"warning":"Performance audit is not available for a website that is not live."},{"strategy":"DESKTOP","status":"UNAVAILABLE","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":{},"warning":"Performance audit is not available for a website that is not live."}]
        for a in perf: db.add(PerformanceAudit(project_id=p.id,analysis_run_id=run.id,strategy=a["strategy"],status=a["status"],performance_score=a.get("performance_score"),accessibility_score=a.get("accessibility_score"),best_practices_score=a.get("best_practices_score"),seo_score=a.get("seo_score"),metrics_json={**a.get("metrics",{}),"statuses":a.get("statuses",{})},warning=a.get("warning")))
        db.commit()
        set_stage(db,j,"WORKLOAD_CALCULATION",3); workload=estimate_workload(payload,p.mode); w=WorkloadEstimate(project_id=p.id,analysis_run_id=run.id,**workload); db.add(w); db.commit()
        set_stage(db,j,"RULE_EVALUATION",4)
        set_stage(db,j,"ML_PREDICTION",5)
        set_stage(db,j,"PRICING_COMPARISON",6)
        set_stage(db,j,"FINAL_SCORING",7); rec_data=build_recommendation(db,payload,workload,tech,perf,inp.completeness_score,p.target_region,p.mode)
        rec=Recommendation(project_id=p.id,analysis_run_id=run.id,recommended_option=rec_data["recommended_option"],overall_score=rec_data["overall_score"],confidence_value=rec_data["confidence"]["value"],confidence_label=rec_data["confidence"]["label"],resource_size=rec_data["resource_size"],estimated_cost=rec_data["estimated_cost"],alternatives=rec_data["alternatives"],reasons=rec_data["reasons"],assumptions=rec_data["assumptions"],warnings=rec_data["warnings"],rule_results=rec_data["rule_results"],model_version=rec_data["model_version"],model_probabilities=rec_data["model_probabilities"]); db.add(rec); db.flush()
        for s in rec_data["scores"]: db.add(RecommendationScore(recommendation_id=rec.id,**s))
        db.add(ModelPrediction(analysis_run_id=run.id,predicted_class=rec_data["recommended_option"],probabilities=rec_data["model_probabilities"],features=rec_data["model_features"],model_version_id=rec_data["model_version_id"])); db.commit()
        set_stage(db,j,"CONFIDENCE_CALCULATION",8)
        set_stage(db,j,"OPTIMIZATION_GENERATION",9); opts=generate_optimizations(perf,tech,workload,rec_data["recommended_option"])
        for o in opts: db.add(Optimization(project_id=p.id,analysis_run_id=run.id,status="OPEN",**o))
        db.commit(); set_stage(db,j,"REPORT_PREPARATION",10); generate_report(db,p,p.user_id)
        j.status="COMPLETED"; j.progress=100; j.current_stage="REPORT_PREPARATION"; j.completed_at=utcnow(); j.stages_json=[{"name":x,"status":"COMPLETED"} for x in ALL_STAGES]; run.status="COMPLETED"; run.completed_at=utcnow(); p.status="COMPLETED"
        create_notification(db,p.user_id,"ANALYSIS_COMPLETED","Analysis completed",f"{p.title} is ready to review.",{"project_id":p.id,"job_id":j.id}); db.add(AuditLog(actor_user_id=p.user_id,action="ANALYSIS_COMPLETED",entity_type="PROJECT",entity_id=p.id,metadata_json={"job_id":j.id,"run_id":run.id})); db.commit(); return j
    except AppError as exc:
        if exc.code=="ANALYSIS_CANCELLED":
            run.status="CANCELLED"; run.completed_at=utcnow(); p.status="CANCELLED"; db.commit(); return j
        j.status="FAILED"; j.error_code=exc.code; j.error_message=exc.message[:500]; j.completed_at=utcnow(); run.status="FAILED"; run.completed_at=utcnow(); p.status="FAILED"; create_notification(db,p.user_id,"ANALYSIS_FAILED","Analysis failed",exc.message,{"project_id":p.id,"job_id":j.id}); db.commit(); return j
    except Exception as exc:
        db.rollback()
        logger.exception("Analysis pipeline failed", extra={"job_id":job_id})
        j=_job(db,job_id); p=db.get(Project,j.project_id); run=db.get(AnalysisRun,j.analysis_run_id)
        j.status="FAILED"; j.error_code="ANALYSIS_FAILED"; j.error_message="The analysis failed because an internal processing step could not complete."; j.completed_at=utcnow(); run.status="FAILED"; run.completed_at=utcnow(); p.status="FAILED"; create_notification(db,p.user_id,"ANALYSIS_FAILED","Analysis failed",j.error_message,{"project_id":p.id,"job_id":j.id}); db.commit(); return j

def status_payload(j:AnalysisJob):
    completed=sum(1 for x in (j.stages_json or []) if x.get("status")=="COMPLETED")
    return {"job_id":j.id,"project_id":j.project_id,"analysis_run_id":j.analysis_run_id,"status":j.status,"current_stage":j.current_stage,"completed_stages":completed,"total_stages":len(ALL_STAGES),"progress":j.progress,"stages":j.stages_json or [],"error_code":j.error_code,"error_message":j.error_message}
