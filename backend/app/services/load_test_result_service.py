from __future__ import annotations
from datetime import datetime,timezone,timedelta
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import LoadTestPlan,LoadTestResult,LoadTestEnvironment,LoadTestResourceMetric,AuditLog,Notification,TestResult
from app.services.load_test_result_parser import parse_summary
from app.services.load_test_validation_service import analyse

def _limit(db:Session,user_id:str):
    since=datetime.now(timezone.utc)-timedelta(hours=1)
    count=db.scalar(select(func.count(AuditLog.id)).where(AuditLog.actor_user_id==user_id,AuditLog.action=="LOAD_TEST_RESULT_IMPORTED",AuditLog.created_at>=since)) or 0
    if count>=settings.k6_result_import_limit_per_hour:raise AppError("RATE_LIMITED","The hourly result-import safety limit has been reached. Try again later.",429)

def _environment(db:Session,plan_id:str)->dict:
    row=db.scalar(select(LoadTestEnvironment).where(LoadTestEnvironment.load_test_plan_id==plan_id))
    return {"hosting_type":row.hosting_type,"vcpu":row.vcpu,"ram_gb":row.ram_gb,"database_type":row.database_type,"cdn_enabled":row.cdn_enabled,"notes":row.notes} if row else {}

def serialize_result(row:LoadTestResult,plan_public_id:str|None=None)->dict:
    return {"id":row.public_id,"planId":plan_public_id or row.load_test_plan_id,"sourceType":row.source_type,"overallStatus":row.overall_status,"aiValidationStatus":row.ai_validation_status,"totalRequests":row.total_requests,"peakVus":row.peak_vus,"averageRps":row.average_rps,"averageMs":row.http_req_duration_avg_ms,"p50Ms":row.http_req_duration_p50_ms,"p90Ms":row.http_req_duration_p90_ms,"p95Ms":row.http_req_duration_p95_ms,"p99Ms":row.http_req_duration_p99_ms,"errorRate":row.http_req_failed_rate,"checksPassed":row.checks_passed,"checksFailed":row.checks_failed,"thresholdsPassed":row.thresholds_passed,"analysis":row.analysis_json,"createdAt":row.created_at.isoformat()}

def import_result(db:Session,plan:LoadTestPlan,user_id:str,data:dict,resource_metrics:dict|None=None,source_type:str="K6_SUMMARY_JSON")->dict:
    _limit(db,user_id);metrics=parse_summary(data);resource_metrics={k:v for k,v in (resource_metrics or {}).items() if v is not None}
    if source_type=="K6_MANAGED_SUMMARY" and not metrics.get("peak_vus"):
        metrics["peak_vus"]=plan.virtual_users
    predicted={"vcpu":plan.recommended_vcpu,"ram_gb":plan.recommended_ram_gb}
    analysis=analyse(metrics,plan.response_time_threshold_ms,plan.error_rate_threshold,_environment(db,plan.id),predicted,plan.virtual_users,resource_metrics,plan.estimated_rps,plan.peak_rps)
    if source_type=="K6_MANAGED_SUMMARY":
        analysis["reasons"]=[reason for reason in analysis.get("reasons",[]) if not reason.startswith("The website result is valid, but tested CPU/RAM")]
        analysis["evidence_note"]="This genuine k6 summary measures public-page latency, throughput, checks, and failures under the bounded scenario. PageSpeed/Lighthouse separately measures frontend experience. Private CPU, RAM, and database saturation still require monitoring evidence."
        analysis["execution_mode"]="MANAGED_K6"
    result=LoadTestResult(load_test_plan_id=plan.id,project_id=plan.project_id,analysis_run_id=plan.analysis_run_id,source_type=source_type,**metrics,thresholds_passed=analysis["overall_status"]=="PASS",overall_status=analysis["overall_status"],ai_validation_status=analysis["ai_validation_status"],analysis_json=analysis,raw_summary_json=data)
    db.add(result);db.flush();plan.status="RESULT_IMPORTED"
    if resource_metrics:db.add(LoadTestResourceMetric(load_test_result_id=result.id,**resource_metrics))
    test_name="Managed k6 Load Test" if source_type=="K6_MANAGED_SUMMARY" else "Authorized k6 Load Test"
    completion_action="LOAD_TEST_MANAGED_COMPLETED" if source_type=="K6_MANAGED_SUMMARY" else "LOAD_TEST_RESULT_IMPORTED"
    db.add(TestResult(test_type="ST",test_name=test_name,status="PASSED" if result.overall_status=="PASS" else "FAILED",details={"load_test_result_id":result.public_id,"project_id":plan.project_id,"source_type":source_type}))
    db.add(AuditLog(actor_user_id=user_id,action=completion_action,entity_type="PROJECT",entity_id=plan.project_id,metadata_json={"plan_id":plan.public_id,"result_id":result.public_id,"source_type":source_type}))
    db.add(AuditLog(actor_user_id=user_id,action="LOAD_TEST_THRESHOLD_PASSED" if result.thresholds_passed else "LOAD_TEST_THRESHOLD_FAILED",entity_type="PROJECT",entity_id=plan.project_id,metadata_json={"result_id":result.public_id}))
    db.add(AuditLog(actor_user_id=user_id,action="LOAD_TEST_ANALYSIS_COMPLETED",entity_type="PROJECT",entity_id=plan.project_id,metadata_json={"result":result.overall_status,"validation":result.ai_validation_status}))
    db.add(Notification(user_id=user_id,type="LOAD_TEST_RESULT",title="Load-test result analysis completed",message=f"Result: {result.overall_status}",data={"project_id":plan.project_id,"plan_id":plan.public_id,"result_id":result.public_id}))
    plan.status="ANALYSED";db.commit();return serialize_result(result,plan.public_id)
