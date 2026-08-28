from sqlalchemy.orm import Session
from app.services.ml_service import build_model_features, predict, predict_resources
from app.services.scoring_service import score_options, resource_size
from app.services.pricing_service import PricingService
from app.services.confidence_service import calculate
from app.services.cost_optimization_service import optimize_cost
from app.services.openrouter_explanation_service import explain as explain_with_llm

DISPLAY={"VPS":"VPS","CLOUD_VM":"Cloud VM","KUBERNETES":"Kubernetes"}

def technology_quality(tech:list[dict])->float:
    vals=[float(x.get("confidence",0)) for x in tech if x.get("technology") and "No reliable" not in x.get("technology","")]
    return sum(vals)/len(vals) if vals else 0.35

def performance_quality(perf:list[dict])->float:
    available=[row for row in perf if row.get("status")=="AVAILABLE"]
    if not available:return .25
    states=[((row.get("metrics") or {}).get("core_web_vitals") or {}).get("overall_status") for row in available]
    if "PASSED" in states:return .95
    if "FAILED" in states:return .85
    return .55

def cost_for_option(pricing:PricingService,option:str,resources:dict):
    plans=pricing.options(option,resources["vcpu"],resources["ram_gb"])
    if not plans: return {"currency":"USD","min":None,"max":None,"pricing_updated_at":None,"plans":[],"warning":"No stored USD pricing plan matches the requested size."}
    lo=min(p["monthlyRange"][0] for p in plans); hi=max(p["monthlyRange"][1] for p in plans[:3]); newest=max(p["updatedAt"] for p in plans)
    estimated=any(p.get("isEstimate") for p in plans)
    warning="No exact stored SKU met the model-sized resources; this range is transparently extrapolated from stored same-architecture pricing and must be verified before purchase." if estimated else "Stored demo pricing is being used; replace it with verified provider pricing before a purchase decision." if any(p.get("isDemo") for p in plans) else None
    return {"currency":"USD","min":round(lo,2),"max":round(hi,2),"pricing_updated_at":newest,"pricing_method":"RESOURCE_RATIO_EXTRAPOLATION" if estimated else "EXACT_STORED_PLAN_MATCH","evidence":"EXTRAPOLATED_STORED_PRICING" if estimated else "STORED_PROVIDER_PRICING","plans":plans[:3],"warning":warning}

def build(db:Session,payload:dict,workload:dict,tech:list[dict],perf:list[dict],input_completeness:float,mode:str|None=None):
    project_mode=str(mode or payload.get("project_mode") or payload.get("mode") or "PLANNED").upper()
    features=build_model_features(payload,workload,tech,perf,project_mode)
    ml=predict(db,features,workload,payload); resources=predict_resources(features,workload) or {**resource_size(workload,payload),"model_source":"RULE_FALLBACK","model_version":"RESOURCE_RULE_FALLBACK"}; pricing=PricingService(db)
    cost_map={o:cost_for_option(pricing,o,resources) for o in ["VPS","CLOUD_VM","KUBERNETES"]}
    scores=score_options(workload,payload,ml,[],cost_map)
    winner=ml["predicted_class"]
    if winner not in DISPLAY:
        raise ValueError("The classifier returned an unsupported hosting class.")
    winning=next(score for score in scores if score["option"]==winner)
    price_fresh=pricing.freshness(sum([cost_map[o]["plans"] for o in cost_map],[]))
    ml_certainty=max(ml["probabilities"].values()) if ml.get("probabilities") else 0.3
    conf=calculate(ml_certainty,input_completeness,technology_quality(tech),performance_quality(perf),float(workload.get("evidence_quality",0.5)),price_fresh)
    warnings=[]
    if performance_quality(perf)<0.5: warnings.append("Performance data was unavailable, so the recommendation has lower confidence.")
    if cost_map[winner].get("warning"): warnings.append(cost_map[winner]["warning"])
    alternatives=[]
    for s in scores:
        c=cost_map[s["option"]]
        alternatives.append({"rank":s["rank"],"option":s["option"],"display_name":DISPLAY[s["option"]],"score":s["score"],"estimated_monthly_range":[c["min"],c["max"]],"currency":"USD","pricing_status":s["cost_analysis"]["status"],"pricing_evidence":s["cost_analysis"]["evidence"],"cost_midpoint":s["cost_analysis"]["midpoint"],"score_breakdown":s["score_breakdown"],"scalability":{"VPS":"Moderate","CLOUD_VM":"High","KUBERNETES":"Very High"}[s["option"]],"complexity":{"VPS":"Low","CLOUD_VM":"Medium","KUBERNETES":"High"}[s["option"]],"maintenance":{"VPS":"Manual","CLOUD_VM":"Flexible","KUBERNETES":"High"}[s["option"]],"availability":{"VPS":"Limited","CLOUD_VM":"Strong","KUBERNETES":"Excellent"}[s["option"]],"fit_reasons":[f"Classifier probability: {s['ml_probability']:.1%}"],"weaknesses":[]})
    cost_note={"WITHIN_BUDGET":"The complete stored monthly range fits the supplied budget.","PARTIALLY_WITHIN_BUDGET":"The minimum fits, while variable usage may exceed the budget.","OVER_BUDGET":"Even the stored minimum is above the supplied budget.","BUDGET_NOT_PROVIDED":"No budget was supplied; the classifier selection remains unchanged.","PRICING_UNAVAILABLE":"No matching stored provider range exists; no price was invented."}[winning["cost_analysis"]["status"]]
    reasons=[{"label":"Trained Logistic Regression prediction","score":winning["score"],"note":f"The classifier selected {DISPLAY[winner]} from the submitted input features with {winning['ml_probability']:.1%} probability."},{"label":"Cost information","score":None,"note":cost_note}]
    selected_cost={k:v for k,v in cost_map[winner].items() if k not in {"plans","warning"}}
    cost_optimization=optimize_cost(payload,winner,resources,selected_cost,cost_map[winner]["plans"])
    decision_evidence={
        "method":"TRAINED_LOGISTIC_REGRESSION_ARGMAX",
        "decision_boundary":"The configured trained Logistic Regression classifier predicts the hosting option directly from user-derived features. Pricing, resource sizing, static descriptions, and the LLM cannot modify the selected option.",
        "classifier":{"output":ml.get("predicted_class"),"probabilities":ml.get("probabilities",{}),"version":ml.get("model_version"),"source":"TRAINED_LOGISTIC_REGRESSION"},
        "resource_sizer":{"output":resources,"version":resources.get("model_version"),"source":resources.get("model_source","RULE_FALLBACK")},
        "rules":{"count":0,"applied":[],"selection_effect":"DISABLED"},
        "pricing":{"source":"STORED_PROVIDER_PRICING","matching_plans":len(cost_map[winner]["plans"]),"updated_at":selected_cost.get("pricing_updated_at")},
    }
    llm_context={
        "input_summary":{key:features.get(key) for key in ("monthly_users","expected_concurrent_users","peak_rps","budget_usd","storage_gb","growth_rate","operational_skill","availability_level","project_mode","app_type")},
        "model_outputs":decision_evidence,
        "decision":{"recommended_option":winner,"score":winning["score"],"confidence":conf,"estimated_cost":selected_cost,"resources":resources,"alternatives":alternatives,"reasons":reasons,"assumptions":workload.get("assumptions",[])},
        "cost_optimization":cost_optimization,
    }
    llm_explanation=explain_with_llm(llm_context)
    if llm_explanation.get("warning") and llm_explanation.get("status") not in {"DISABLED"}:
        warnings.append(llm_explanation["warning"])
    return {"recommended_option":winner,"overall_score":winning["score"],"confidence":conf,"resource_size":resources,"estimated_cost":selected_cost,"cost_optimization":cost_optimization,"decision_evidence":decision_evidence,"llm_explanation":llm_explanation,"alternatives":alternatives,"reasons":reasons,"assumptions":workload.get("assumptions",[]),"warnings":warnings,"rule_results":[],"ranking_method":{"method":"TRAINED_LOGISTIC_REGRESSION_ARGMAX","weights":winning["score_breakdown"]["weights"],"tie_breakers":[],"options_ranked":3},"model_version":ml.get("model_version"),"model_version_id":ml.get("model_version_id"),"model_features":features,"model_probabilities":ml.get("probabilities",{}),"scores":scores,"provider_options":cost_map[winner]["plans"]}

def technology_suggestion(payload:dict):
    idea=(payload.get("idea") or payload.get("description") or "").lower(); features=" ".join(payload.get("features",[]) if isinstance(payload.get("features"),list) else [str(payload.get("features") or "")]).lower()
    frontend=[{"technology":"Next.js","score":90,"reason":"Strong fit for full-stack web applications, server rendering and a modern React frontend."}]
    backend=[{"technology":"FastAPI","score":88,"reason":"Good fit for API-heavy applications and AI/ML service integration."}]
    database=[{"technology":"PostgreSQL","score":88,"reason":"Reliable default for transactional application data and rich query capability."}]
    supporting=[{"technology":"Redis","score":80,"reason":"Useful for caching, rate limiting and background job coordination."}]
    if "chat" in features or "real-time" in idea: supporting.append({"technology":"WebSocket service","score":84,"reason":"The idea includes real-time interaction."})
    if "video" in idea or "stream" in idea: supporting.append({"technology":"Object storage + CDN","score":93,"reason":"Media workloads should be served outside the application server."})
    return {"frontend":frontend,"backend":backend,"database":database,"supporting_services":supporting,"method":"DETERMINISTIC_RULES"}
