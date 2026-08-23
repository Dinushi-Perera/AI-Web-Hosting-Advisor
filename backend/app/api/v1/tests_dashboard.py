from fastapi import APIRouter,Depends
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import TestResult,MLModelVersion,Feedback
router=APIRouter(prefix="/testing",tags=["Testing"])
@router.get("/summary")
def summary(user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=list(db.scalars(select(TestResult).order_by(TestResult.executed_at.desc()).limit(500))); counts={}
    for r in rows: counts.setdefault(r.test_type,{"total":0,"passed":0,"failed":0});counts[r.test_type]["total"]+=1;counts[r.test_type]["passed" if r.status.upper()=="PASSED" else "failed"]+=1
    return {"byType":counts,"results":[{"id":r.id,"testType":r.test_type,"testName":r.test_name,"status":r.status,"executedAt":r.executed_at.isoformat(),"durationMs":r.duration_ms,"details":r.details} for r in rows]}
@router.get("/model-evaluation")
def model_eval(user=Depends(get_current_user),db:Session=Depends(get_db)):
    m=db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)).order_by(MLModelVersion.created_at.desc()))
    if not m:return {"activeModel":None,"message":"No trained model is active. Recommendation uses deterministic fallback scoring."}
    return {"activeModel":{"id":m.id,"version":m.version,"algorithm":m.algorithm,"accuracy":m.accuracy,"precision":m.precision,"recall":m.recall,"f1":m.f1,"confusionMatrix":m.confusion_matrix,"classDistribution":m.class_distribution}}
@router.get("/uat/summary")
def uat(user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=list(db.scalars(select(Feedback)))
    if not rows:return {"count":0,"clarity":None,"usefulness":None,"easeOfUse":None,"trust":None}
    avg=lambda k:round(sum(getattr(x,k) for x in rows)/len(rows),2)
    return {"count":len(rows),"clarity":avg("clarity_rating"),"usefulness":avg("usefulness_rating"),"easeOfUse":avg("ease_of_use_rating"),"trust":avg("recommendation_trust_rating")}
