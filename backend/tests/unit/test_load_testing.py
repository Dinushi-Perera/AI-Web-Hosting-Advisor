import json
from pathlib import Path
import pytest
from app.core.exceptions import AppError
from app.services.load_test_planner_service import build_plan
from app.services.k6_script_generator import generate_script,safe_filename
from app.services.load_test_result_parser import parse_summary
from app.services.load_test_validation_service import analyse
from app.services.url_security_service import validate_public_url_redirects
from app.schemas.load_test import LoadTestPlanCreate

FIXTURES=Path(__file__).parents[1]/"fixtures"
CONTEXT={"recommended_target_vus":300,"expected_concurrent_users":300,"estimated_rps":40,"peak_rps":60,"warnings":[],"ai_context":{"hosting":"CLOUD_VM","vcpu":4,"ram_gb":8}}

def test_load_stages_are_gradual_and_end_at_zero():
    plan=build_plan(CONTEXT,"LOAD",300,None)
    values=[x["target_virtual_users"] for x in plan["stages"]]
    assert values[-1]==0
    assert max(values)==300
    assert values[:4]==sorted(values[:4])

def test_vus_above_safe_limit_is_capped_in_planner():
    plan=build_plan({**CONTEXT,"warnings":[]},"LOAD",999,None)
    assert plan["target_virtual_users"]==500
    assert any("capped" in w.lower() for w in plan["warnings"])

def test_requested_duration_is_distributed_across_stages():
    plan=build_plan(CONTEXT,"LOAD",300,420)
    assert plan["duration_seconds"]==420
    assert sum(x["duration_seconds"] for x in plan["stages"])==420

def test_script_is_explainable_and_safe():
    plan=build_plan(CONTEXT,"LOAD",300,None)
    script=generate_script(project_title="Shop Demo",project_id="p-1",target_url="https://example.com",test_type="LOAD",context=CONTEXT,plan=plan,p95_ms=2000,error_rate=.01,think_min=1,think_max=3,safe_paths=["/","/products"])
    assert "AI Recommendation: CLOUD_VM" in script
    assert "Run only against systems" in script
    assert "sleep(randomIntBetween(1, 3))" in script
    assert "http.get" in script

def test_filename_is_sanitized():assert safe_filename("../../My Shop!!!","abcdef00-x")=="my-shop-load-test-abcdef00.js"

def test_result_parser_and_pass_logic():
    parsed=parse_summary(json.loads((FIXTURES/"k6_summary_pass.json").read_text()))
    assert parsed["http_req_duration_p95_ms"]==1420
    assert parsed["http_req_failed_rate"]==.004
    result=analyse(parsed,2000,.01,{"vcpu":4,"ram_gb":8},{"vcpu":4,"ram_gb":8},300)
    assert result["overall_status"]=="PASS"
    assert result["ai_validation_status"]=="SUPPORTED"

def test_failed_result_does_not_claim_specific_bottleneck():
    parsed=parse_summary(json.loads((FIXTURES/"k6_summary_fail.json").read_text()))
    result=analyse(parsed,2000,.01,{})
    assert result["overall_status"]=="FAIL"
    assert result["ai_validation_status"]=="INSUFFICIENT_EVIDENCE"
    assert "CPU capacity" not in " ".join(result["reasons"])

def test_invalid_summary_is_rejected():
    with pytest.raises(AppError):parse_summary({"metrics":{}})

def test_missing_checks_are_rejected():
    data=json.loads((FIXTURES/"k6_summary_pass.json").read_text())
    del data["metrics"]["checks"]
    with pytest.raises(AppError):parse_summary(data)

def test_current_machine_readable_k6_summary_is_parsed():
    data={"config":{"duration":5},"results":{"metrics":[
        {"name":"http_reqs","values":{"count":10}},
        {"name":"iterations","values":{"count":10}},
        {"name":"http_req_duration","values":{"avg":120,"min":80,"med":110,"max":220,"p(90)":180,"p(95)":200,"p(99)":218}},
        {"name":"http_req_failed","values":{"matches":0,"total":10,"rate":0}},
        {"name":"vus_max","values":{"value":2,"max":2}},
    ],"checks":{"metrics":[
        {"name":"checks_succeeded","values":{"matches":10,"total":10,"rate":1}},
        {"name":"checks_failed","values":{"matches":0,"total":10,"rate":0}},
    ],"results":[{"name":"status is successful","passes":10,"fails":0}]}}}
    parsed=parse_summary(data)
    assert parsed["total_requests"]==10
    assert parsed["average_rps"]==2
    assert parsed["checks_passed"]==10
    assert parsed["peak_vus"]==2

def test_partial_pass_when_only_checks_fail():
    parsed=parse_summary(json.loads((FIXTURES/"k6_summary_pass.json").read_text()))
    parsed["checks_failed"]=1
    result=analyse(parsed,2000,.01,{"vcpu":4,"ram_gb":8},{"vcpu":4,"ram_gb":8},300)
    assert result["overall_status"]=="PARTIAL_PASS"
    assert result["ai_validation_status"]=="PARTIALLY_SUPPORTED"

def test_resource_prediction_requires_matching_environment_and_workload():
    parsed=parse_summary(json.loads((FIXTURES/"k6_summary_pass.json").read_text()))
    mismatch=analyse(parsed,2000,.01,{"vcpu":2,"ram_gb":4},{"vcpu":4,"ram_gb":8},300)
    assert mismatch["ai_validation_status"]=="INSUFFICIENT_EVIDENCE"
    parsed["peak_vus"]=100
    incomplete=analyse(parsed,2000,.01,{"vcpu":4,"ram_gb":8},{"vcpu":4,"ram_gb":8},300)
    assert incomplete["ai_validation_status"]=="INSUFFICIENT_EVIDENCE"

def test_unsafe_paths_and_invalid_think_time_are_rejected():
    base={"authorization_confirmed":True,"risk_acknowledged":True,"target_url":"https://example.com"}
    with pytest.raises(ValueError):LoadTestPlanCreate(**base,safe_paths=["/%61dmin/users"])
    with pytest.raises(ValueError):LoadTestPlanCreate(**base,think_time_min_seconds=5,think_time_max_seconds=1)

def test_private_redirect_target_is_rejected(monkeypatch):
    class Response:
        status_code=302
        headers={"location":"http://127.0.0.1/admin"}
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def request(self,*args,**kwargs):return Response()
    monkeypatch.setattr("app.services.url_security_service._host_ips",lambda host:{"8.8.8.8"})
    monkeypatch.setattr("app.services.url_security_service.httpx.Client",Client)
    with pytest.raises(AppError) as error:validate_public_url_redirects("https://example.com")
    assert error.value.code=="URL_BLOCKED"
