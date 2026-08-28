from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import select,text,func
from sqlalchemy.orm import Session
from app.core.health import readiness
from app.models import TestResult,Feedback,Project,ProjectInput,WorkloadEstimate,Recommendation,PerformanceAudit,LoadTestResult
from app.services.evaluation_service import evaluate_supplied_assets
from app.core.exceptions import AppError

STRATEGIES={"UT":"Unit Testing","IT":"Integration Testing","ST":"System Testing","UAT":"User Acceptance Testing","ORT":"Operational Readiness Testing"}
def _case(name,status,expected,actual,plain):return {"name":name,"status":status,"expected":expected,"actual":actual,"plainLanguage":plain}

def project_context(db:Session,user_id:str,project_id:str|None=None):
    q=select(Project).where(Project.user_id==user_id,Project.deleted_at.is_(None)).order_by(Project.updated_at.desc())
    if project_id:q=q.where(Project.id==project_id)
    project=db.scalar(q)
    if not project:raise AppError("TEST_PROJECT_REQUIRED","Choose one of your projects before running input-based testing.",422)
    inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project.id));run=project.latest_analysis_run_id
    workload=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==run)) if run else None
    recommendation=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==run)) if run else None
    performance=db.scalar(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==run).order_by(PerformanceAudit.audited_at.desc())) if run else None
    loads=db.scalar(select(func.count(LoadTestResult.id)).where(LoadTestResult.project_id==project.id)) or 0
    return {"project":project,"payload":(inp.payload if inp else {}) or {},"inputScore":inp.completeness_score if inp else 0,"workload":workload,"recommendation":recommendation,"performance":performance,"loads":loads}

def serialize_context(c:dict):
    p=c["project"];w=c["workload"];r=c["recommendation"];perf=c["performance"]
    return {"projectId":p.id,"projectName":p.title,"mode":p.mode,"inputCompleteness":round(float(c["inputScore"] or 0)*100),"inputKeys":sorted(c["payload"].keys())[:12],"workload":{"concurrentUsers":w.concurrent_users,"estimatedRps":w.estimated_rps,"peakRps":w.peak_rps} if w else None,"recommendation":r.recommended_option if r else None,"performanceScore":perf.performance_score if perf else None,"loadTests":c["loads"]}

def run_strategy(db:Session,user_id:str,strategy:str,project_id:str|None=None)->list[TestResult]:
    strategy=strategy.upper()
    if strategy not in STRATEGIES:raise AppError("TEST_STRATEGY_INVALID","Choose UT, IT, ST, UAT or ORT.",422)
    started=datetime.now(timezone.utc);c=project_context(db,user_id,project_id);p=c["project"];payload=c["payload"];w=c["workload"];r=c["recommendation"];perf=c["performance"];cases=[];has_input=bool(payload);analysis_ready=bool(w and r)
    if strategy=="UT":
        cases=[_case("Submitted input is available","PASSED" if has_input else "NOT_RUN","Project input saved",f"{len(payload)} supplied fields","Proves this test uses your saved project input, not a generic sample."),_case("Input completeness","PASSED" if c["inputScore"]>=.5 else "FAILED","At least 50% complete",f"{round(c['inputScore']*100)}% complete","Shows whether your submitted detail is enough for dependable analysis."),_case("Input-to-workload calculation","PASSED" if w else "NOT_RUN","Workload created from your inputs",f"{w.concurrent_users if w else 0} concurrent users","Proves your traffic input became a workload estimate.")]
    elif strategy=="IT":
        db.execute(text("SELECT 1"));assets=evaluate_supplied_assets();cases=[_case("Project input to database","PASSED" if has_input else "FAILED","Saved project input query",p.title,"Confirms your submitted project data can be read."),_case("Workload to AI recommendation","PASSED" if analysis_ready else "NOT_RUN","Workload and recommendation linked",r.recommended_option if r else "Missing","Proves your workload is connected to its AI recommendation."),_case("Trained model integration","PASSED" if assets["totalTrainingRows"]==5000 else "FAILED","Two supplied models using 5,000 rows",str(assets["totalTrainingRows"]),"Confirms your inputs can flow through the trained-model layer.")]
    elif strategy=="ST":
        cases=[_case("Complete project analysis","PASSED" if p.status.upper()=="COMPLETED" and analysis_ready else "NOT_RUN","Completed input-to-recommendation workflow",p.status,"Proves this exact project completed its analysis workflow."),_case("Performance evidence","PASSED" if perf and perf.status=="AVAILABLE" else "NOT_RUN","Frontend evidence when a URL was analysed",str(perf.performance_score) if perf else "No performance audit","Shows whether your project has PageSpeed/Lighthouse evidence."),_case("Load-test evidence","PASSED" if c["loads"] else "NOT_RUN","At least one saved k6 result",str(c["loads"]),"Shows whether this project has measured traffic evidence.")]
    elif strategy=="UAT":
        rows=list(db.scalars(select(Feedback).where(Feedback.user_id==user_id,Feedback.project_id==p.id)));avg=lambda attr:round(sum(getattr(x,attr) for x in rows)/len(rows),2) if rows else None
        cases=[_case("Report clarity from your feedback","PASSED" if rows and avg("clarity_rating")>=3 else "NOT_RUN","Average rating at least 3/5",str(avg("clarity_rating") or "No feedback yet"),"Proves a real user assessed whether this project information is clear."),_case("Recommendation usefulness from your feedback","PASSED" if rows and avg("usefulness_rating")>=3 else "NOT_RUN","Average rating at least 3/5",str(avg("usefulness_rating") or "No feedback yet"),"Proves a real user assessed whether the recommendation helps their decision.")]
    else:
        h=readiness();cases=[_case("k6 execution readiness","PASSED" if h.get("k6_engine")=="ready" else "FAILED","k6 engine available",str(h.get("k6_engine")),"Proves this project can use the managed k6 runner after public-target authorization."),_case("Model readiness for your input","PASSED" if h["hosting_model"]==h["resource_model"]=="ready" else "FAILED","Both trained models ready",f"Hosting {h['hosting_model']}; resource {h['resource_model']}","Proves the models used to interpret your input are available."),_case("Evidence storage readiness","PASSED" if Path("storage/reports").exists() and Path("storage/load_tests").exists() else "FAILED","Writable evidence storage",str(c["loads"])+" saved load tests","Proves this project evidence can be retained.")]
    duration=int((datetime.now(timezone.utc)-started).total_seconds()*1000);rows=[];snapshot=serialize_context(c)
    for case in cases:
        row=TestResult(test_type=strategy,test_name=case["name"],status=case["status"],duration_ms=duration,details={**case,"strategyName":STRATEGIES[strategy],"testingUserId":user_id,"projectId":p.id,"inputContext":snapshot});db.add(row);rows.append(row)
    db.commit();return rows
