from sqlalchemy.orm import Session
from app.services.rule_engine import evaluate
from app.services.ml_service import predict
from app.services.scoring_service import score_options, resource_size
from app.services.pricing_service import PricingService
from app.services.confidence_service import calculate

DISPLAY={"VPS":"VPS","CLOUD_VM":"Cloud VM","KUBERNETES":"Kubernetes"}

def technology_quality(tech:list[dict])->float:
    vals=[float(x.get("confidence",0)) for x in tech if x.get("technology") and "No reliable" not in x.get("technology","")]
    return sum(vals)/len(vals) if vals else 0.35

def performance_quality(perf:list[dict])->float: return 0.9 if any(x.get("status")=="AVAILABLE" for x in perf) else 0.25

def cost_for_option(pricing:PricingService,option:str,resources:dict,region:str|None):
    plans=pricing.options(option,resources["vcpu"],resources["ram_gb"],region)
    if not plans: return {"currency":"USD","min":None,"max":None,"pricing_updated_at":None,"plans":[],"warning":"No stored USD pricing plan matches the requested size."}
    lo=min(p["monthlyRange"][0] for p in plans); hi=max(p["monthlyRange"][1] for p in plans[:3]); newest=max(p["updatedAt"] for p in plans)
    warning="Stored demo pricing is being used; replace it with verified provider pricing before a purchase decision." if any(p.get("isDemo") for p in plans) else None
    return {"currency":"USD","min":round(lo,2),"max":round(hi,2),"pricing_updated_at":newest,"plans":plans[:3],"warning":warning}

def build(db:Session,payload:dict,workload:dict,tech:list[dict],perf:list[dict],input_completeness:float,region:str|None=None):
    rules=evaluate(payload,workload)
    features={"expected_concurrent_users":workload.get("concurrent_users",0),"estimated_rps":workload.get("estimated_rps",0),"peak_rps":workload.get("peak_rps",0),"budget":payload.get("budget") or payload.get("monthly_budget") or 0,"app_type":payload.get("category") or payload.get("websiteType") or "OTHER","database_intensity":workload.get("database_intensity","MEDIUM"),"storage_gb":workload.get("storage_gb",0),"growth_rate":workload.get("growth_level","UNKNOWN"),"operational_skill":"ADVANCED" if payload.get("kubernetesSkill") else "BEGINNER"}
    ml=predict(db,features,workload,payload); scores=score_options(workload,payload,ml,rules); winner=scores[0]["option"]; resources=resource_size(workload,payload); pricing=PricingService(db)
    cost_map={o:cost_for_option(pricing,o,resources,region) for o in ["VPS","CLOUD_VM","KUBERNETES"]}
    price_fresh=pricing.freshness(sum([cost_map[o]["plans"] for o in cost_map],[]))
    ml_certainty=max(ml["probabilities"].values()) if ml.get("probabilities") else 0.3
    if not ml.get("is_trained_model"): ml_certainty=min(ml_certainty,0.65)
    conf=calculate(ml_certainty,input_completeness,technology_quality(tech),performance_quality(perf),float(workload.get("evidence_quality",0.5)),price_fresh)
    warnings=[]
    if not ml.get("is_trained_model"): warnings.append("No active trained ML artifact was available; deterministic fallback scoring was used and confidence is capped accordingly.")
    if performance_quality(perf)<0.5: warnings.append("Performance data was unavailable, so the recommendation has lower confidence.")
    if cost_map[winner].get("warning"): warnings.append(cost_map[winner]["warning"])
    alternatives=[]
    for s in scores:
        c=cost_map[s["option"]]
        alternatives.append({"option":s["option"],"display_name":DISPLAY[s["option"]],"score":s["score"],"estimated_monthly_range":[c["min"],c["max"]],"currency":"USD","scalability":{"VPS":"Moderate","CLOUD_VM":"High","KUBERNETES":"Very High"}[s["option"]],"complexity":{"VPS":"Low","CLOUD_VM":"Medium","KUBERNETES":"High"}[s["option"]],"maintenance":{"VPS":"Manual","CLOUD_VM":"Flexible","KUBERNETES":"High"}[s["option"]],"availability":{"VPS":"Limited","CLOUD_VM":"Strong","KUBERNETES":"Excellent"}[s["option"]],"fit_reasons":[r["reason"] for r in rules if r["option"]==s["option"] and r["score_delta"]>0],"weaknesses":[r["reason"] for r in rules if r["option"]==s["option"] and r["score_delta"]<0]})
    reasons=[{"label":"Traffic fit","score":scores[0]["traffic_fit"],"note":"Derived from estimated peak requests per second."},{"label":"Budget fit","score":scores[0]["budget_fit"],"note":"Compared against the user-declared USD monthly budget."},{"label":"Scalability","score":scores[0]["scalability_fit"],"note":"Scores ability to handle expected growth without unnecessary complexity."},{"label":"Operational fit","score":scores[0]["operational_fit"],"note":"Accounts for the declared operational experience."}]
    return {"recommended_option":winner,"overall_score":scores[0]["score"],"confidence":conf,"resource_size":resources,"estimated_cost":{k:v for k,v in cost_map[winner].items() if k!="plans" and k!="warning"},"alternatives":alternatives,"reasons":reasons,"assumptions":workload.get("assumptions",[]),"warnings":warnings,"rule_results":rules,"model_version":ml.get("model_version"),"model_probabilities":ml.get("probabilities",{}),"scores":scores,"provider_options":cost_map[winner]["plans"]}

def technology_suggestion(payload:dict):
    idea=(payload.get("idea") or payload.get("description") or "").lower(); features=" ".join(payload.get("features",[]) if isinstance(payload.get("features"),list) else [str(payload.get("features") or "")]).lower()
    frontend=[{"technology":"Next.js","score":90,"reason":"Strong fit for full-stack web applications, server rendering and a modern React frontend."}]
    backend=[{"technology":"FastAPI","score":88,"reason":"Good fit for API-heavy applications and AI/ML service integration."}]
    database=[{"technology":"PostgreSQL","score":88,"reason":"Reliable default for transactional application data and rich query capability."}]
    supporting=[{"technology":"Redis","score":80,"reason":"Useful for caching, rate limiting and background job coordination."}]
    if "chat" in features or "real-time" in idea: supporting.append({"technology":"WebSocket service","score":84,"reason":"The idea includes real-time interaction."})
    if "video" in idea or "stream" in idea: supporting.append({"technology":"Object storage + CDN","score":93,"reason":"Media workloads should be served outside the application server."})
    return {"frontend":frontend,"backend":backend,"database":database,"supporting_services":supporting,"method":"DETERMINISTIC_RULES"}
