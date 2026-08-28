OPTIONS=["VPS","CLOUD_VM","KUBERNETES"]
WEIGHTS={"trained_logistic_regression_probability":1.0}

def _clamp(value):return max(0,min(100,float(value)))
def _number(value,default=0.0):
    try:return float(value)
    except (TypeError,ValueError):return default

def resource_size(workload:dict,payload:dict):
    peak=_number(workload.get("peak_rps"));db=str(workload.get("database_intensity") or "MEDIUM")
    if peak<30:vcpu,ram=2,4
    elif peak<150:vcpu,ram=4,8
    elif peak<500:vcpu,ram=8,16
    else:vcpu,ram=16,32
    if db in {"HIGH","VERY_HIGH"}:ram*=1.5
    storage=max(40,int(_number(workload.get("storage_gb"),50)))
    return {"vcpu":vcpu,"ram_gb":int(ram),"storage_gb":storage,"transfer_tb":max(1,round(_number(workload.get("bandwidth_gb"),500)/1000,1))}

def cost_fit(cost:dict|None,budget:float)->dict:
    """Score a complete monthly range without inventing a price when evidence is absent."""
    cost=cost or {};lo=cost.get("min");hi=cost.get("max")
    if lo is None or hi is None:
        return {"score":55.0,"status":"PRICING_UNAVAILABLE","range":{"min":None,"max":None},"midpoint":None,"budget":budget or None,"evidence":"UNAVAILABLE"}
    lo=max(0,_number(lo));hi=max(lo,_number(hi));mid=round((lo+hi)/2,2)
    if not budget:
        score,status=75.0,"BUDGET_NOT_PROVIDED"
    elif hi<=budget:
        score,status=100.0,"WITHIN_BUDGET"
    elif lo<=budget:
        position=(budget-lo)/max(hi-lo,1);score=70+position*25;status="PARTIALLY_WITHIN_BUDGET"
    else:
        over=(lo-budget)/max(budget,1);score=_clamp(65-over*100);status="OVER_BUDGET"
    return {"score":round(score,1),"status":status,"range":{"min":round(lo,2),"max":round(hi,2)},"midpoint":mid,"budget":budget or None,"evidence":cost.get("evidence","STORED_PROVIDER_PRICING")}

def score_options(workload:dict,payload:dict,ml:dict,rules:list,option_costs:dict|None=None):
    del workload, rules
    budget=_number(payload.get("budget") or payload.get("monthly_budget"))
    results=[]
    for option in OPTIONS:
        ml_fit=_clamp(_number((ml.get("probabilities") or {}).get(option))*100)
        pricing=cost_fit((option_costs or {}).get(option),budget)
        # These rows are persisted for transparent comparison only. Cost and
        # operational fields remain informational and cannot affect rank.
        results.append({"option":option,"score":round(ml_fit,4),"ml_probability":round(ml_fit/100,6),"budget_fit":pricing["score"],"traffic_fit":0.0,"scalability_fit":0.0,"reliability_fit":0.0,"operational_fit":0.0,"cost_analysis":pricing,"score_breakdown":{"method":"TRAINED_LOGISTIC_REGRESSION_PROBABILITY_ONLY","weights":WEIGHTS,"model_probability":round(ml_fit/100,6),"final_score":round(ml_fit,4)},"rule_adjustments":[]})
    results.sort(key=lambda row:(-row["score"], row["option"]))
    for index,row in enumerate(results,1):row["rank"]=index
    return results
