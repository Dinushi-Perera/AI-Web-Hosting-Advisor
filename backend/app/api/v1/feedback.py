from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.models import Feedback,AuditLog,Notification
from app.schemas.analysis import FeedbackRequest
router=APIRouter(tags=["Testing"])
@router.post("/projects/{project_id}/feedback",status_code=201)
def feedback(project_id:str,req:FeedbackRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); f=Feedback(user_id=user.id,project_id=p.id,**req.model_dump());db.add(f);db.add(AuditLog(actor_user_id=user.id,action="UAT_FEEDBACK_SUBMITTED",entity_type="PROJECT",entity_id=p.id,metadata_json={"clarity":req.clarity_rating,"usefulness":req.usefulness_rating,"trust":req.recommendation_trust_rating}));db.add(Notification(user_id=user.id,type="FEEDBACK_SAVED",title="Evaluation feedback saved",message=f"Your UAT feedback for {p.title} was saved.",data={"project_id":p.id}));db.commit(); return {"id":f.id,"success":True}
