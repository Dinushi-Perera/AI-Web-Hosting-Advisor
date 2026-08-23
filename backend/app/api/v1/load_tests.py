from pathlib import Path
from fastapi import APIRouter,Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import AppError
from app.models import LoadTestPlan
from app.schemas.analysis import LoadTestPlanRequest
from app.services.load_test_service import generate
router=APIRouter(tags=["Load Testing"])
@router.post("/projects/{project_id}/load-test-plan",status_code=201)
def create_plan(project_id:str,req:LoadTestPlanRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return generate(db,p,user.id,req)
@router.get("/load-test-plans/{plan_id}")
def get_plan(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(LoadTestPlan,plan_id)
    if not r or r.user_id!=user.id: raise AppError("LOAD_TEST_PLAN_NOT_FOUND","Load-test plan not found.",404)
    return {"plan_id":r.id,"test_type":r.test_type,"virtual_users":r.virtual_users,"duration_seconds":r.duration_seconds,"target_url":r.target_url,"stages":r.stages,"script":r.script,"safety_notes":r.safety_notes}
@router.get("/load-test-plans/{plan_id}/download")
def download(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(LoadTestPlan,plan_id)
    if not r or r.user_id!=user.id: raise AppError("LOAD_TEST_PLAN_NOT_FOUND","Load-test plan not found.",404)
    path=Path(settings.load_test_storage_dir)/Path(r.file_key or "").name
    if not path.exists(): raise AppError("FILE_NOT_FOUND","Generated script file is unavailable.",404)
    return FileResponse(path,media_type="application/javascript",filename="authorized-load-test.js")
