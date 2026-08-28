import json
from datetime import datetime,timezone
from pathlib import Path
from fastapi import APIRouter,Depends,UploadFile,File,Form,Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import LoadTestPlan,LoadTestResult,AuditLog
from app.repositories.load_test_repository import get_plan,list_results
from app.schemas.load_test import LoadTestPlanCreate,LoadTestResourceMetricsInput
from app.services.load_test_service import generate,generate_and_run_managed,recommendation,serialize_plan,history,comparison
from app.services.load_test_result_service import serialize_result,import_result

router=APIRouter(tags=["Load Testing"])

def owned_plan(db:Session,plan_id:str,user_id:str)->LoadTestPlan:
    row=get_plan(db,plan_id,user_id)
    if not row:raise AppError("LOAD_TEST_PLAN_NOT_FOUND","Load-test plan not found.",404)
    return row

@router.get("/projects/{project_id}/load-test/recommendation")
def get_recommendation(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return recommendation(db,owned_project(db,project_id,user))

@router.post("/projects/{project_id}/load-test-plan",status_code=201)
def create_plan(project_id:str,req:LoadTestPlanCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return generate(db,owned_project(db,project_id,user),user.id,req)

@router.post("/projects/{project_id}/load-test/run-managed",status_code=201)
def run_managed(project_id:str,req:LoadTestPlanCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return generate_and_run_managed(db,owned_project(db,project_id,user),user.id,req)

@router.get("/projects/{project_id}/load-test-plans")
@router.get("/projects/{project_id}/load-tests/history")
def project_history(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    project=owned_project(db,project_id,user);return history(db,project.id,user.id)

@router.get("/load-test-plans/{plan_id}")
def get_plan_details(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return serialize_plan(db,owned_plan(db,plan_id,user.id),include_script=True)

@router.get("/load-test-plans/{plan_id}/download")
def download(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_plan(db,plan_id,user.id)
    if not row.file_key:raise AppError("FILE_NOT_FOUND","Generated script file is unavailable.",404)
    path=Path(settings.load_test_storage_dir)/"scripts"/Path(row.file_key).name
    if not path.is_file():raise AppError("FILE_NOT_FOUND","Generated script file is unavailable.",404)
    row.status="DOWNLOADED";row.downloaded_at=datetime.now(timezone.utc);db.add(AuditLog(actor_user_id=user.id,action="LOAD_TEST_SCRIPT_DOWNLOADED",entity_type="PROJECT",entity_id=row.project_id,metadata_json={"plan_id":row.public_id}));db.commit()
    return FileResponse(path,media_type="application/javascript",filename=Path(row.file_key).name)

@router.post("/load-test-plans/{plan_id}/results",status_code=201)
async def upload_result(plan_id:str,result:UploadFile=File(...),resource_metrics:str|None=Form(default=None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_plan(db,plan_id,user.id)
    if result.content_type not in {"application/json","text/json"}:raise AppError("INVALID_FILE_TYPE","Only a k6 JSON summary file is accepted.",422)
    maximum=settings.k6_result_max_file_mb*1024*1024;content=await result.read(maximum+1)
    if len(content)>maximum:raise AppError("RESULT_FILE_TOO_LARGE",f"Result files cannot exceed {settings.k6_result_max_file_mb} MB.",413)
    try:data=json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError):raise AppError("INVALID_JSON","The uploaded result is not valid UTF-8 JSON.",422)
    metrics={}
    if resource_metrics:
        try:metrics=LoadTestResourceMetricsInput.model_validate_json(resource_metrics).model_dump(exclude_none=True)
        except Exception:raise AppError("INVALID_RESOURCE_METRICS","Optional resource metrics are invalid.",422)
    return import_result(db,row,user.id,data,metrics)

@router.get("/load-test-plans/{plan_id}/results")
def plan_results(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=owned_plan(db,plan_id,user.id);return [serialize_result(x,row.public_id) for x in list_results(db,row.id)]

@router.get("/load-test-results/{result_id}")
def result_details(result_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.scalar(select(LoadTestResult).join(LoadTestPlan,LoadTestPlan.id==LoadTestResult.load_test_plan_id).where(((LoadTestResult.id==result_id)|(LoadTestResult.public_id==result_id)),LoadTestPlan.user_id==user.id))
    if not row:raise AppError("LOAD_TEST_RESULT_NOT_FOUND","Load-test result not found.",404)
    plan=db.get(LoadTestPlan,row.load_test_plan_id);return serialize_result(row,plan.public_id if plan else None)

@router.get("/projects/{project_id}/load-tests/compare")
def compare(project_id:str,first:str=Query(...),second:str=Query(...),user=Depends(get_current_user),db:Session=Depends(get_db)):
    project=owned_project(db,project_id,user);return comparison(db,project.id,user.id,first,second)
