from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project
from app.core.database import get_db
from app.models import CloudProvider,Recommendation
from app.services.pricing_service import PricingService
from app.core.exceptions import AppError
router=APIRouter(tags=["Pricing"])
@router.get("/pricing")
def frontend_pricing(provider:str|None=None,region:str|None=None,architecture:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    plans=PricingService(db).list_plans(architecture,region); return [p for p in plans if not provider or p["provider"].lower()==provider.lower()]
@router.get("/pricing/providers")
def providers(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return [{"id":p.id,"name":p.name,"slug":p.slug} for p in PricingService(db).providers()]
@router.get("/pricing/plans")
def plans(provider:str|None=None,region:str|None=None,architecture:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)): return frontend_pricing(provider,region,architecture,user,db)
@router.get("/pricing/plans/{plan_id}")
def plan(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=PricingService(db).list_plans(); r=next((x for x in rows if x["id"]==plan_id),None)
    if not r: raise AppError("PRICING_PLAN_NOT_FOUND","Pricing plan not found.",404)
    return r
@router.get("/pricing/compare")
def price_compare(architecture:str|None=None,region:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)): return {"currency":"USD","plans":PricingService(db).list_plans(architecture,region)}
@router.get("/projects/{project_id}/cost")
def cost(project_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user)
    if not p.latest_analysis_run_id: raise AppError("RECOMMENDATION_NOT_FOUND","Recommendation is not ready.",404)
    r=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==p.latest_analysis_run_id))
    if not r: raise AppError("RECOMMENDATION_NOT_FOUND","Recommendation is not ready.",404)
    cost=r.estimated_cost or {}; budget=None
    from app.api.v1.helpers import project_payload
    payload=project_payload(db,p.id)
    try: budget=float(payload.get("budget") or payload.get("monthly_budget"))
    except Exception: budget=None
    lo,hi=cost.get("min"),cost.get("max"); status="UNKNOWN" if budget is None or hi is None else "WITHIN_BUDGET" if hi<=budget else "PARTIALLY_WITHIN_BUDGET" if lo is not None and lo<=budget else "OVER_BUDGET"
    components=[]
    if lo is not None and hi is not None:
        components=[{"name":"Compute","min":round(lo*0.6,2),"max":round(hi*0.6,2),"status":"ESTIMATED"},{"name":"Database / storage / backups / monitoring","min":round(lo*0.4,2),"max":round(hi*0.4,2),"status":"ESTIMATED"}]
    return {"currency":"USD","recommended_range":{"min":lo,"max":hi},"budget":budget,"budget_status":status,"components":components,"providers":PricingService(db).options(r.recommended_option,r.resource_size.get("vcpu",1),r.resource_size.get("ram_gb",1),p.target_region),"pricing_updated_at":cost.get("pricing_updated_at"),"warnings":r.warnings}
