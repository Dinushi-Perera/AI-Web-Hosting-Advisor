from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project,run_id_for,project_payload
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import Recommendation,RecommendationScore,ProjectInput
from app.services.explanation_service import recommendation_explanation
from app.services.architecture_service import build_architecture
from app.services.clarification_service import questions
from app.services.recommendation_service import technology_suggestion
from app.schemas.analysis import PreferredOptionRequest
from app.services.analysis_pipeline import start_analysis
from app.workers.analysis_tasks import enqueue_analysis
router=APIRouter(tags=["Recommendations"])
def rec_json(r:Recommendation):
    return {"id":r.id,"recommended_option":r.recommended_option,"recommended": {"VPS":"VPS","CLOUD_VM":"Cloud VM","KUBERNETES":"Kubernetes"}.get(r.recommended_option,r.recommended_option),"overall_score":r.overall_score,"fitScore":r.overall_score,"confidence":{"value":r.confidence_value,"label":r.confidence_label},"confidencePercent":round(r.confidence_value*100),"resource_size":r.resource_size,"resources":{"vcpu":r.resource_size.get("vcpu"),"ramGb":r.resource_size.get("ram_gb"),"storageGb":r.resource_size.get("storage_gb"),"transferTb":r.resource_size.get("transfer_tb")},"estimated_cost":r.estimated_cost,"alternatives":r.alternatives,"reasons":r.reasons,"assumptions":r.assumptions,"warnings":r.warnings,"model_version":r.model_version,"model_probabilities":r.model_probabilities,"currency":"USD"}
@router.get("/projects/{project_id}/recommendation")
def recommendation(project_id:str,run_id:str|None=Query(None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rid=run_id_for(p,run_id); r=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==rid))
    if not r: raise AppError("RECOMMENDATION_NOT_FOUND","Recommendation is not ready.",404)
    out=rec_json(r); out["stale"]=p.recommendation_stale; out["userPreferredOption"]=p.user_preferred_option; return out
@router.get("/projects/{project_id}/recommendation/explanation")
def explanation(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    data=recommendation(project_id,None,user,db); return recommendation_explanation({"recommended_option":data["recommended_option"],"alternatives":data["alternatives"],"reasons":data["reasons"],"assumptions":data["assumptions"],"warnings":data["warnings"]})
@router.get("/projects/{project_id}/recommendation/compare")
def compare(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    data=recommendation(project_id,None,user,db); return {"currency":"USD","options":data["alternatives"]}
@router.get("/projects/{project_id}/recommendation/missing-inputs")
def missing(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return {"questions":questions(project_payload(db,p.id))}
@router.post("/projects/{project_id}/recommendation/recalculate",status_code=202)
def recalc(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); j=start_analysis(db,p); enqueue_analysis(j.id); return {"projectId":p.id,"jobId":j.id,"status":"QUEUED"}
@router.post("/projects/{project_id}/recommendation/preference")
def preference(project_id:str,req:PreferredOptionRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); o=req.option.upper().replace(" ","_")
    if o not in {"VPS","CLOUD_VM","KUBERNETES"}: raise AppError("VALIDATION_ERROR","Choose VPS, Cloud VM or Kubernetes.",422)
    p.user_preferred_option=o; db.commit(); return {"systemRecommendation":recommendation(project_id,None,user,db)["recommended_option"],"userPreferredOption":o}
@router.get("/projects/{project_id}/architecture")
def architecture(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); data=recommendation(project_id,None,user,db); return build_architecture(data["recommended_option"],project_payload(db,p.id))
@router.post("/projects/{project_id}/clarification-questions")
def clarification(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return {"questions":questions(project_payload(db,p.id))}
@router.get("/projects/{project_id}/technology-suggestion")
def tech_suggest(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); return technology_suggestion(project_payload(db,p.id))
