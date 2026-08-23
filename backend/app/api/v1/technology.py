from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project,run_id_for
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import TechnologyDetection,TechnologyEvidence
from app.schemas.analysis import CorrectionRequest
router=APIRouter(tags=["Technology"])
@router.get("/projects/{project_id}/technology")
def get_technology(project_id:str,run_id:str|None=Query(None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rid=run_id_for(p,run_id); rows=list(db.scalars(select(TechnologyDetection).where(TechnologyDetection.analysis_run_id==rid)))
    out=[]
    for t in rows:
        ev=list(db.scalars(select(TechnologyEvidence).where(TechnologyEvidence.detection_id==t.id)))
        out.append({"id":t.id,"category":t.category,"technology":t.technology,"confidence":round(t.confidence*100),"confidenceValue":t.confidence,"status":t.confidence_label.title(),"evidence":[e.pattern for e in ev],"evidenceDetails":[{"source":e.source,"pattern":e.pattern,"weight":e.weight} for e in ev],"correction":t.user_correction})
    return out
@router.post("/projects/{project_id}/technology/{detection_id}/feedback")
def correction(project_id:str,detection_id:str,req:CorrectionRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); t=db.get(TechnologyDetection,detection_id)
    if not t or t.project_id!=p.id: raise AppError("DETECTION_NOT_FOUND","Technology detection not found.",404)
    t.user_correction={"actual_technology":req.actual_technology,"reason":req.reason,"source":"USER_CONFIRMED"}; db.commit(); return {"success":True,"detectionId":t.id,"correction":t.user_correction}
