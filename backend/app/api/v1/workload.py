from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project,run_id_for
from app.core.database import get_db
from app.models import WorkloadEstimate
from app.schemas.analysis import WorkloadProfileRequest
from app.services.workload_estimator import estimate_from_profile
router=APIRouter(tags=["Workload"])
@router.get("/projects/{project_id}/workload")
def workload(project_id:str,run_id:str|None=Query(None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rid=run_id_for(p,run_id); w=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==rid))
    if not w:return {}
    return {"concurrent_users":w.concurrent_users,"estimated_rps":w.estimated_rps,"peak_rps":w.peak_rps,"classification":w.classification,"database_intensity":w.database_intensity,"storage_gb":w.storage_gb,"bandwidth_gb":w.bandwidth_gb,"growth_level":w.growth_level,"assumptions":w.assumptions,"evidence_quality":w.evidence_quality}
@router.post("/workload/estimate-from-profile")
def profile(req:WorkloadProfileRequest,user=Depends(get_current_user)): return estimate_from_profile(req.audience_profile,req.application_type)
