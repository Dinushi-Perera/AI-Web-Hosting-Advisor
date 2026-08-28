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
def frontend_pricing(provider:str|None=None,architecture:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    plans=PricingService(db).list_plans(architecture); return [p for p in plans if not provider or p["provider"].lower()==provider.lower()]
@router.get("/pricing/providers")
def providers(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return [{"id":p.id,"name":p.name,"slug":p.slug} for p in PricingService(db).providers()]
@router.get("/pricing/plans")
def plans(provider:str|None=None,architecture:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)): return frontend_pricing(provider,architecture,user,db)
@router.get("/pricing/plans/{plan_id}")
def plan(plan_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=PricingService(db).list_plans(); r=next((x for x in rows if x["id"]==plan_id),None)
    if not r: raise AppError("PRICING_PLAN_NOT_FOUND","Pricing plan not found.",404)
    return r
@router.get("/pricing/compare")
def price_compare(architecture:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)): return {"currency":"USD","plans":PricingService(db).list_plans(architecture)}
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
        shares={"VPS":[("Compute",.65),("Database and storage",.15),("CDN and transfer",.10),("Backups and monitoring",.10)],"CLOUD_VM":[("Compute",.50),("Database and storage",.25),("CDN and transfer",.12),("Backups and monitoring",.13)],"KUBERNETES":[("Cluster compute",.55),("Database and storage",.20),("Network and delivery",.10),("Operations and monitoring",.15)]}.get(r.recommended_option,[("Compute",.6),("Supporting services",.4)])
        components=[{"name":name,"min":round(lo*share,2),"max":round(hi*share,2),"share":round(share*100),"status":"ESTIMATED"} for name,share in shares]
    providers=PricingService(db).options(r.recommended_option,r.resource_size.get("vcpu",1),r.resource_size.get("ram_gb",1))
    utilization=None if not budget or hi is None else round(hi/budget*100,1)
    gap=None if budget is None or hi is None else round(budget-hi,2)
    budget_tier="NOT_PROVIDED" if budget is None else "STARTER" if budget<50 else "GROWTH" if budget<150 else "SCALE"
    explanation={"WITHIN_BUDGET":"The full recommended monthly range fits inside the supplied budget.","PARTIALLY_WITHIN_BUDGET":"The lower estimate fits, but optional or variable services may exceed the supplied budget.","OVER_BUDGET":"The stored pricing range exceeds the supplied budget; review the cheaper provider plans or reduce optional services.","UNKNOWN":"A budget or complete price range is unavailable."}[status]
    ranked=[]
    for item in sorted(r.alternatives or [],key=lambda row:row.get("rank",99)):
        monthly=item.get("estimated_monthly_range") or [None,None]
        ranked.append({"rank":item.get("rank"),"architecture":item.get("option"),"display_name":item.get("display_name"),"fit_score":item.get("score"),"monthly_range":{"min":monthly[0],"max":monthly[1]},"annual_range":{"min":round(monthly[0]*12,2) if monthly[0] is not None else None,"max":round(monthly[1]*12,2) if monthly[1] is not None else None},"budget_status":item.get("pricing_status"),"pricing_evidence":item.get("pricing_evidence"),"score_breakdown":item.get("score_breakdown")})
    annual={"min":round(lo*12,2) if lo is not None else None,"max":round(hi*12,2) if hi is not None else None}
    return {"currency":"USD","architecture":r.recommended_option,"resources":r.resource_size,"recommended_range":{"min":lo,"max":hi},"annual_range":annual,"budget":budget,"budget_tier":budget_tier,"budget_status":status,"budget_utilization_percent":utilization,"budget_headroom":gap,"budget_explanation":explanation,"cost_optimization":r.cost_optimization,"decision_evidence":r.decision_evidence,"llm_explanation":r.llm_explanation,"llm_status":r.llm_status,"llm_model":r.llm_model or (r.llm_explanation or {}).get("configured_model"),"components":components,"component_method":"ARCHITECTURE_ALLOCATION_ESTIMATE","ranked_options":ranked,"providers":providers,"matching_provider_count":len(providers),"pricing_updated_at":cost.get("pricing_updated_at"),"warnings":r.warnings}
