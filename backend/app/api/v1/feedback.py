from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.models import Feedback
from app.schemas.analysis import FeedbackRequest
router=APIRouter(tags=["Testing"])
@router.post("/projects/{project_id}/feedback",status_code=201)
def feedback(project_id:str,req:FeedbackRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); f=Feedback(user_id=user.id,project_id=p.id,**req.model_dump()); db.add(f); db.commit(); return {"id":f.id,"success":True}
