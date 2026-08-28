from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import Project,ProjectInput,WorkloadEstimate,Recommendation,PerformanceAudit

READABLE=(1,5,10,25,50,75,100,150,200,250,300,400,500)

def _readable(value:int,target:int)->int:
    value=max(1,min(value,target))
    return min(READABLE,key=lambda n:abs(n-value)) if target in READABLE or value<target else target

def _requests_per_user(payload:dict,concurrent:int,rps:float)->float:
    raw=payload.get("requestsPerUser") or payload.get("requests_per_user_per_minute")
    try:return round(float(raw),2)
    except (TypeError,ValueError):return round((rps*60/max(concurrent,1)),2)

def _test_type(workload:WorkloadEstimate,payload:dict)->tuple[str,str]:
    growth=str(workload.growth_level or "").upper(); pattern=str(payload.get("trafficPattern") or payload.get("traffic_pattern") or "").lower()
    if "event" in pattern or "spike" in pattern:return "SPIKE","Event-driven or sudden traffic makes a short controlled spike test useful."
    if workload.concurrent_users:return "LOAD",f"Expected concurrency of {workload.concurrent_users} users makes a normal load test the most useful first capacity test."
    if growth in {"HIGH","RAPID"}:return "SPIKE","High growth makes a safe spike scenario useful after smoke verification."
    return "SMOKE","Begin with basic endpoint verification before increasing workload."

def _stage_values(test_type:str,target:int)->list[tuple[int,int,str]]:
    if test_type=="SMOKE":return [(30,min(5,target),"RAMP_UP"),(30,min(5,target),"HOLD"),(15,0,"RAMP_DOWN")]
    if test_type=="SPIKE":return [(30,_readable(ceil(target*.10),target),"RAMP_UP"),(20,target,"PEAK"),(45,target,"HOLD"),(30,_readable(ceil(target*.10),target),"RAMP_DOWN"),(20,0,"RAMP_DOWN")]
    if test_type=="SOAK":return [(60,_readable(ceil(target*.25),target),"RAMP_UP"),(60,_readable(ceil(target*.50),target),"RAMP_UP"),(600,_readable(ceil(target*.50),target),"HOLD"),(60,0,"RAMP_DOWN")]
    percentages=(.25,.50,.75,1.0,1.10,1.20) if test_type=="STRESS" else (.10,.25,.50,.75,1.0)
    values=[min(target,_readable(ceil(target*p),target)) for p in percentages]
    if test_type=="STRESS": values=[min(settings.k6_max_vus,_readable(ceil(target*p),min(settings.k6_max_vus,ceil(target*p)))) for p in percentages]
    stages=[]
    for i,value in enumerate(values):stages.append((30 if i<2 else 60,value,"PEAK" if i==len(values)-1 else "RAMP_UP"))
    stages.extend([(60,values[-1],"HOLD"),(30,0,"RAMP_DOWN")])
    return stages

def context(db:Session,project:Project)->dict:
    if not project.latest_analysis_run_id:raise AppError("ANALYSIS_REQUIRED","Complete an analysis before generating a load-test plan.",409)
    run=project.latest_analysis_run_id
    workload=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==run))
    recommendation=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==run))
    inputs=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project.id))
    perf=db.scalar(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==run,PerformanceAudit.status=="AVAILABLE").order_by(PerformanceAudit.audited_at.desc()))
    if not workload or not recommendation:raise AppError("ANALYSIS_INCOMPLETE","Workload and AI recommendation results are required.",409)
    payload=inputs.payload if inputs else {}
    concurrent=max(1,int(workload.concurrent_users or 1));rpm=_requests_per_user(payload,concurrent,float(workload.estimated_rps or 0))
    estimated=round(concurrent*rpm/60,2); peak_multiplier=round(float(workload.peak_rps or estimated)/max(estimated,.01),2);peak=round(estimated*peak_multiplier,2)
    resources=recommendation.resource_size or {}; test_type,reason=_test_type(workload,payload);performance_metrics=perf.metrics_json if perf else {}
    expected=concurrent;target=min(expected,settings.k6_max_vus);warnings=[]
    if expected>settings.k6_max_vus:warnings.append("Expected production concurrency is higher than the configured safe prototype testing limit. The generated scenario uses the safe configured maximum.")
    return {"analysis_run_id":run,"project_mode":project.mode,"recommended_test_type":test_type,"reason":reason,"expected_concurrent_users":expected,"requests_per_user_per_minute":rpm,"estimated_rps":estimated,"peak_rps":peak,"peak_multiplier":peak_multiplier,"traffic_classification":workload.classification,"recommended_target_vus":target,"recommended_duration_seconds":270,"thresholds":{"p95_ms":settings.k6_default_p95_threshold_ms,"p99_ms":settings.k6_default_p99_threshold_ms,"error_rate":settings.k6_default_error_rate_threshold,"check_pass_rate":settings.k6_default_check_pass_rate},"ai_context":{"hosting":recommendation.recommended_option,"vcpu":resources.get("vcpu") or resources.get("recommended_vcpu"),"ram_gb":resources.get("ram_gb") or resources.get("ramGb") or resources.get("recommended_ram_gb"),"confidence":recommendation.confidence_value},"performance_score":perf.performance_score if perf else None,"performance_context":{"available":bool(perf),"source":perf.source if perf else None,"performance_score":perf.performance_score if perf else None,"lcp_ms":performance_metrics.get("lcp_ms"),"inp_ms":performance_metrics.get("inp_ms"),"cls":performance_metrics.get("cls"),"tbt_ms":performance_metrics.get("tbt_ms"),"ttfb_ms":performance_metrics.get("ttfb_ms"),"core_web_vitals":performance_metrics.get("core_web_vitals") or {}},"calculation":{"requests_per_minute":round(concurrent*rpm,2),"estimated_rps_formula":f"{concurrent} × {rpm} ÷ 60 = {estimated}","peak_rps_formula":f"{estimated} × {peak_multiplier} = {peak}"},"warnings":warnings,"project_updated_at":project.updated_at.isoformat()}

def build_plan(context_data:dict,test_type:str,target_vus:int|None,duration_seconds:int|None)->dict:
    if test_type=="STRESS" and not settings.k6_allow_stress_test or test_type=="SPIKE" and not settings.k6_allow_spike_test or test_type=="SOAK" and not settings.k6_allow_soak_test:raise AppError("LOAD_TEST_TYPE_DISABLED","This test type is disabled by backend safety policy.",422)
    requested=target_vus or context_data["recommended_target_vus"]
    target=min(requested,settings.k6_max_vus);warnings=list(context_data["warnings"])
    if requested>settings.k6_max_vus:warnings.append(f"Target VUs were capped at the backend safety maximum of {settings.k6_max_vus}.")
    stages=_stage_values(test_type,target)
    if duration_seconds:
        desired=min(duration_seconds,settings.k6_max_duration_seconds);base=sum(s[0] for s in stages);scaled=[]
        for d,v,kind in stages:scaled.append((max(1,round(d*desired/base)),v,kind))
        difference=desired-sum(s[0] for s in scaled);d,v,kind=scaled[-2];scaled[-2]=(max(1,d+difference),v,kind);stages=scaled
    if sum(s[0] for s in stages)>settings.k6_max_duration_seconds:raise AppError("LOAD_TEST_LIMIT_EXCEEDED","Generated duration exceeds the backend safety maximum.",422)
    return {"test_type":test_type,"target_virtual_users":target,"duration_seconds":sum(s[0] for s in stages),"stages":[{"stage_order":i+1,"duration_seconds":d,"target_virtual_users":v,"stage_type":kind} for i,(d,v,kind) in enumerate(stages)],"warnings":warnings}
