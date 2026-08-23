from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.analytics_service import dashboard
router=APIRouter(tags=["Dashboard"])
@router.get("/dashboard")
def dash(user=Depends(get_current_user),db:Session=Depends(get_db)): return dashboard(db,user)
@router.get("/dashboard/performance")
def dash_perf(range:str=Query("30d",pattern="^(7d|30d|90d|all)$"),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return dashboard(db,user)["performance_trend"]
@router.get("/demo/scenarios")
def demos(user=Depends(get_current_user)):
    return [{"id":"demo-live","mode":"LIVE_URL","title":"Authorized Live Site Sample","is_demo":True,"note":"Run only against a site you own or are authorized to analyse."},{"id":"demo-planned","mode":"PLANNED","title":"Planned E-commerce Sample","is_demo":True},{"id":"demo-idea","mode":"NEW_IDEA","title":"New SaaS Idea Sample","is_demo":True}]
