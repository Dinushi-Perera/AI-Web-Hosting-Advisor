from fastapi import APIRouter,Depends,Query
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.models import TestResult,MLModelVersion,Feedback
from app.services.ml_service import bundled_model_status
from app.services.evaluation_service import evaluate_supplied_assets
from app.services.testing_strategy_service import run_strategy,STRATEGIES,project_context,serialize_context
router=APIRouter(prefix="/testing",tags=["Testing"])
@router.get("/summary")
def summary(project_id:str|None=Query(default=None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=[r for r in db.scalars(select(TestResult).order_by(TestResult.executed_at.desc()).limit(500)) if r.details.get("testingUserId")==user.id and (not project_id or r.details.get("projectId")==project_id)]; counts={}
    aliases={"UNIT":"UT","INTEGRATION":"IT","SYSTEM":"ST"}
    for r in rows:
        key=aliases.get(r.test_type,r.test_type);counts.setdefault(key,{"total":0,"passed":0,"failed":0,"notRun":0});counts[key]["total"]+=1
        bucket="passed" if r.status.upper()=="PASSED" else "notRun" if r.status.upper() in {"NOT_RUN","SKIPPED","WARNING"} else "failed";counts[key][bucket]+=1
    return {"strategies":STRATEGIES,"byType":counts,"inputContext":serialize_context(project_context(db,user.id,project_id)),"results":[{"id":r.id,"testType":aliases.get(r.test_type,r.test_type),"testName":r.test_name,"status":r.status,"executedAt":r.executed_at.isoformat(),"durationMs":r.duration_ms,"details":r.details} for r in rows]}
@router.post("/run/{strategy}")
def execute_strategy(strategy:str,project_id:str|None=Query(default=None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=run_strategy(db,user.id,strategy,project_id);return {"strategy":strategy.upper(),"executed":len(rows),"results":[{"id":r.id,"name":r.test_name,"status":r.status,"details":r.details} for r in rows]}
@router.get("/model-evaluation")
def model_eval(user=Depends(get_current_user),db:Session=Depends(get_db)):
    measured=evaluate_supplied_assets()
    bundled=bundled_model_status()
    m=db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)).order_by(MLModelVersion.created_at.desc()))
    if not m:
        classifier=bundled["classifier"]
        active={"id":None,"version":classifier["version"],"algorithm":classifier["algorithm"],"accuracy":classifier["accuracy"],"precision":None,"recall":None,"f1":classifier["f1"],"confusionMatrix":[],"classDistribution":{},"source":"BUNDLED_ARTIFACT"} if classifier["available"] else None
        return {"activeModel":measured["classifier"] if active else None,"resourceModel":measured["resource"],"datasets":measured["datasets"],"validationRows":measured["validationRows"],"explanation":measured["explanation"],"message":None if active else "No trained model artifact is available. Recommendation uses deterministic fallback scoring."}
    return {"activeModel":measured["classifier"],"resourceModel":measured["resource"],"datasets":measured["datasets"],"validationRows":measured["validationRows"],"explanation":measured["explanation"]}
@router.get("/uat/summary")
def uat(project_id:str|None=Query(default=None),user=Depends(get_current_user),db:Session=Depends(get_db)):
    query=select(Feedback).where(Feedback.user_id==user.id)
    if project_id:
        owned_project(db,project_id,user)
        query=query.where(Feedback.project_id==project_id)
    rows=list(db.scalars(query))
    if not rows:return {"count":0,"clarity":None,"usefulness":None,"easeOfUse":None,"trust":None}
    avg=lambda k:round(sum(getattr(x,k) for x in rows)/len(rows),2)
    return {"count":len(rows),"clarity":avg("clarity_rating"),"usefulness":avg("usefulness_rating"),"easeOfUse":avg("ease_of_use_rating"),"trust":avg("recommendation_trust_rating"),"recentComments":[{"comment":x.comments,"createdAt":x.created_at.isoformat()} for x in rows[-10:] if x.comments]}
