from __future__ import annotations
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import Project,LoadTestPlan,LoadTestStage,LoadTestResult,LoadTestEnvironment,AuditLog,Notification
from app.repositories.load_test_repository import list_project_plans,list_stages,list_results
from app.services.url_security_service import public_host_override,validate_public_url,validate_public_url_redirects
from app.services.load_test_planner_service import context,build_plan
from app.services.k6_script_generator import generate_script,safe_filename,GENERATOR_VERSION
from app.services.load_test_result_service import serialize_result,import_result
from app.services.k6_execution_service import execute_generated_k6

def _limit(db:Session,user_id:str,action:str,maximum:int):
    since=datetime.now(timezone.utc)-timedelta(hours=1)
    count=db.scalar(select(func.count(AuditLog.id)).where(AuditLog.actor_user_id==user_id,AuditLog.action==action,AuditLog.created_at>=since)) or 0
    if count>=maximum:raise AppError("RATE_LIMITED","The hourly safety limit has been reached. Try again later.",429)

def recommendation(db:Session,project:Project)->dict:return context(db,project)

def generate(db:Session,project:Project,user_id:str,req,managed:bool=False):
    _limit(db,user_id,"LOAD_TEST_PLAN_GENERATED",settings.k6_plan_generation_limit_per_hour)
    if not req.authorization_confirmed or not req.risk_acknowledged:raise AppError("LOAD_TEST_AUTH_REQUIRED","Authorization and risk acknowledgement are required.",422)
    test_type=req.test_type.value;ctx=context(db,project);requested=req.target_virtual_users or req.virtual_users;managed_duration=None
    if managed:
        _limit(db,user_id,"LOAD_TEST_MANAGED_STARTED",settings.managed_load_test_run_limit_per_hour)
        if test_type not in {"SMOKE","LOAD"}:raise AppError("MANAGED_TEST_TYPE_UNSUPPORTED","One-click testing supports Quick Check and Normal Traffic modes only.",422)
        requested=min(requested or ctx["recommended_target_vus"],settings.managed_load_test_max_concurrency)
        managed_duration=min(req.duration_seconds or 60,settings.managed_load_test_max_duration_seconds)
    if requested and requested>settings.k6_max_vus:raise AppError("LOAD_TEST_LIMIT_EXCEEDED",f"Target VUs cannot exceed the backend safety maximum of {settings.k6_max_vus}.",422)
    if req.duration_seconds and req.duration_seconds>settings.k6_max_duration_seconds:raise AppError("LOAD_TEST_LIMIT_EXCEEDED","Duration exceeds the backend safety maximum.",422)
    target=validate_public_url(req.target_url)
    if project.mode=="LIVE_URL" and project.website_url and urlsplit(target).hostname!=urlsplit(project.website_url).hostname:raise AppError("LOAD_TEST_DOMAIN_MISMATCH","A live project's target must match its approved website host.",422)
    target=validate_public_url_redirects(target)
    plan=build_plan(ctx,test_type,requested,managed_duration if managed else req.duration_seconds)
    safety_notes=plan["warnings"]+["Run only against systems you own or are explicitly authorized to test."]
    if managed:safety_notes+=[f"The managed k6 test is GET-only and capped at {settings.managed_load_test_max_concurrency} virtual users for {settings.managed_load_test_max_duration_seconds} seconds."]
    else:safety_notes+=["The application generates a script but never executes load tests."]
    workload_snapshot={k:v for k,v in ctx.items() if k not in {"ai_context"}};workload_snapshot["safe_paths"]=req.safe_paths;workload_snapshot["execution_mode"]="MANAGED_K6" if managed else "EXTERNAL_SCRIPT"
    row=LoadTestPlan(project_id=project.id,user_id=user_id,analysis_run_id=ctx["analysis_run_id"],test_type=test_type,virtual_users=plan["target_virtual_users"],duration_seconds=plan["duration_seconds"],target_url=target,authorization_confirmed=True,risk_acknowledged=True,expected_concurrent_users=ctx["expected_concurrent_users"],estimated_rps=ctx["estimated_rps"],peak_rps=ctx["peak_rps"],recommended_hosting=ctx["ai_context"]["hosting"],recommended_vcpu=ctx["ai_context"]["vcpu"],recommended_ram_gb=ctx["ai_context"]["ram_gb"],confidence=ctx["ai_context"]["confidence"],response_time_threshold_ms=req.response_time_threshold_ms,error_rate_threshold=req.error_rate_threshold,stages=plan["stages"],script="",safety_notes=safety_notes,status="READY_TO_RUN" if managed else "GENERATED",generator_version=f"{GENERATOR_VERSION}-managed" if managed else GENERATOR_VERSION,workload_snapshot_json=workload_snapshot,ai_recommendation_snapshot_json=ctx["ai_context"])
    db.add(row);db.flush()
    script=generate_script(project_title=project.title,project_id=project.id,target_url=target,test_type=test_type,context=ctx,plan=plan,p95_ms=req.response_time_threshold_ms,error_rate=req.error_rate_threshold,think_min=req.think_time_min_seconds,think_max=req.think_time_max_seconds,safe_paths=req.safe_paths,host_overrides=public_host_override(target),execution_mode="MANAGED_K6" if managed else "MANUAL")
    filename=safe_filename(project.title,row.public_id);scripts_dir=Path(settings.load_test_storage_dir)/"scripts";scripts_dir.mkdir(parents=True,exist_ok=True);(scripts_dir/filename).write_text(script,encoding="utf-8")
    row.script=script;row.file_key=filename
    for stage in plan["stages"]:db.add(LoadTestStage(load_test_plan_id=row.id,**stage))
    if req.environment:db.add(LoadTestEnvironment(load_test_plan_id=row.id,**req.environment.model_dump()))
    db.add(AuditLog(actor_user_id=user_id,action="LOAD_TEST_PLAN_GENERATED",entity_type="PROJECT",entity_id=project.id,metadata_json={"plan_id":row.public_id,"test_type":test_type,"target_vus":row.virtual_users,"managed":managed}))
    if managed:db.add(AuditLog(actor_user_id=user_id,action="LOAD_TEST_MANAGED_STARTED",entity_type="PROJECT",entity_id=project.id,metadata_json={"plan_id":row.public_id,"target_vus":row.virtual_users}))
    db.add(Notification(user_id=user_id,type="LOAD_TEST_PLAN_READY",title="Website test ready",message=f"{test_type.title()} test prepared for {project.title}.",data={"project_id":project.id,"plan_id":row.public_id,"target_vus":row.virtual_users,"managed":managed}))
    db.commit();return serialize_plan(db,row,include_script=not managed)

def generate_and_run_managed(db:Session,project:Project,user_id:str,req)->dict:
    generated=generate(db,project,user_id,req,managed=True)
    row=db.scalar(select(LoadTestPlan).where(LoadTestPlan.public_id==generated["planId"],LoadTestPlan.user_id==user_id))
    if not row:raise AppError("LOAD_TEST_PLAN_NOT_FOUND","The managed test could not be prepared.",500)
    plan_db_id=row.id
    row.status="RUNNING";db.commit()
    try:
        validate_public_url(row.target_url)
        summary=execute_generated_k6(row.script,row.public_id)
        result=import_result(db,row,user_id,summary,source_type="K6_MANAGED_SUMMARY")
    except Exception as exc:
        db.rollback();row=db.get(LoadTestPlan,plan_db_id)
        if row:
            row.status="RUN_FAILED"
            db.add(AuditLog(actor_user_id=user_id,action="LOAD_TEST_MANAGED_FAILED",entity_type="PROJECT",entity_id=project.id,metadata_json={"plan_id":row.public_id,"error_type":type(exc).__name__}))
            db.add(Notification(user_id=user_id,type="LOAD_TEST_RESULT",title="Website test could not finish",message="The safe website test stopped before a report was created.",data={"project_id":project.id,"plan_id":row.public_id}))
            db.commit()
        if isinstance(exc,AppError):raise
        raise AppError("MANAGED_LOAD_TEST_FAILED","The website test could not finish. Check that the public website is online and try again.",502) from exc
    return {"plan":serialize_plan(db,row),"result":result,"experience":{"executionMode":"MANAGED_K6","engine":"k6","requiresDownload":False,"requiresUpload":False}}

def serialize_plan(db:Session,row:LoadTestPlan,include_script:bool=False)->dict:
    stages=[{"stageOrder":s.stage_order,"durationSeconds":s.duration_seconds,"targetVirtualUsers":s.target_virtual_users,"stageType":s.stage_type} for s in list_stages(db,row.id)]
    results=[serialize_result(x,row.public_id) for x in list_results(db,row.id)];project=db.get(Project,row.project_id)
    out={"planId":row.public_id,"id":row.public_id,"projectId":row.project_id,"analysisRunId":row.analysis_run_id,"testType":row.test_type,"targetUrl":row.target_url,"targetVirtualUsers":row.virtual_users,"durationSeconds":row.duration_seconds,"status":row.status,"executionMode":row.workload_snapshot_json.get("execution_mode","EXTERNAL_SCRIPT"),"authorizationConfirmed":row.authorization_confirmed,"riskAcknowledged":row.risk_acknowledged,"trafficContext":{"expectedConcurrentUsers":row.expected_concurrent_users,"estimatedRps":row.estimated_rps,"peakRps":row.peak_rps,"classification":row.workload_snapshot_json.get("traffic_classification")},"aiContext":{"hosting":row.recommended_hosting,"vcpu":row.recommended_vcpu,"ramGb":row.recommended_ram_gb,"confidence":row.confidence},"thresholds":{"p95Ms":row.response_time_threshold_ms,"errorRate":row.error_rate_threshold},"stages":stages,"filename":safe_filename(project.title if project else "project",row.public_id),"warnings":row.safety_notes,"generatorVersion":row.generator_version,"outdated":bool(project and project.latest_analysis_run_id!=row.analysis_run_id),"results":results,"createdAt":row.created_at.isoformat()}
    if include_script:out["script"]=row.script
    return out

def history(db:Session,project_id:str,user_id:str)->list[dict]:return [serialize_plan(db,p) for p in list_project_plans(db,project_id,user_id)]

def comparison(db:Session,project_id:str,user_id:str,first_id:str,second_id:str)->dict:
    def owned(result_id:str):
        r=db.scalar(select(LoadTestResult).join(LoadTestPlan,LoadTestPlan.id==LoadTestResult.load_test_plan_id).where(((LoadTestResult.id==result_id)|(LoadTestResult.public_id==result_id)),LoadTestResult.project_id==project_id,LoadTestPlan.user_id==user_id))
        if not r:raise AppError("LOAD_TEST_RESULT_NOT_FOUND","Load-test result not found.",404)
        return r
    first,second=owned(first_id),owned(second_id)
    def delta(before,after):return {"before":before,"after":after,"difference":None if before is None or after is None else after-before,"improvementPercent":None if not before or after is None else round((before-after)/before*100,2)}
    first_plan=db.get(LoadTestPlan,first.load_test_plan_id);second_plan=db.get(LoadTestPlan,second.load_test_plan_id)
    return {"first":serialize_result(first,first_plan.public_id if first_plan else None),"second":serialize_result(second,second_plan.public_id if second_plan else None),"p95":delta(first.http_req_duration_p95_ms,second.http_req_duration_p95_ms),"errorRate":delta(first.http_req_failed_rate,second.http_req_failed_rate),"rps":{"before":first.average_rps,"after":second.average_rps,"difference":None if first.average_rps is None or second.average_rps is None else second.average_rps-first.average_rps}}
