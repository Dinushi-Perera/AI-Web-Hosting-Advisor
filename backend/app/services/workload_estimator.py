import math

def _num(v,default=None):
    try:
        if v in (None,"","Unknown","I don't know","Not Decided"): return default
        return float(v)
    except (TypeError,ValueError): return default

def _intensity(payload): return str(payload.get("dbWorkload") or payload.get("database_intensity") or "MEDIUM").upper().replace(" ","_")
def classify(peak_rps:float)->str:
    if peak_rps<20:return "LOW"
    if peak_rps<150:return "MEDIUM"
    if peak_rps<500:return "HIGH"
    return "VERY_HIGH"

def estimate(payload:dict,mode:str)->dict:
    assumptions=[]
    concurrent=_num(payload.get("concurrentUsers") or payload.get("peak_concurrent_users"))
    if concurrent is None:
        audience=str(payload.get("audience") or payload.get("traffic") or payload.get("audience_profile") or "Growing business").lower()
        concurrent=25 if "small" in audience else 100 if "growing" in audience else 300 if "national" in audience else 600 if "international" in audience else 1000
        assumptions.append(f"Concurrent users estimated from audience profile: {int(concurrent)}")
    rpm_per_user=_num(payload.get("requestsPerUser") or payload.get("requests_per_user_per_minute"),10)
    if payload.get("requestsPerUser") in (None,""): assumptions.append("Assumed 10 requests per user per minute")
    peak_multiplier=_num(payload.get("peakMultiplier") or payload.get("peak_multiplier"),1.5)
    if peak_multiplier is None: peak_multiplier=1.5
    base_rpm=concurrent*rpm_per_user; rps=base_rpm/60; peak=rps*peak_multiplier
    storage=_num(payload.get("storage") or payload.get("storage_gb"),50)
    media=str(payload.get("mediaUsage") or payload.get("media_usage") or "Medium").lower()
    monthly=_num(payload.get("monthlyUsers") or payload.get("monthlyVisitors") or payload.get("monthly_visitors"),0)
    bandwidth=max(100.0, monthly*(0.03 if "stream" not in media else 0.5)) if monthly else max(100.0,peak*30)
    quality=0.9 if payload.get("concurrentUsers") not in (None,"") else 0.55
    return {"concurrent_users":int(concurrent),"estimated_rps":round(rps,2),"peak_rps":round(peak,2),"classification":classify(peak),"database_intensity":_intensity(payload),"storage_gb":round(storage or 50,2),"bandwidth_gb":round(bandwidth,2),"growth_level":str(payload.get("growth") or payload.get("growth_level") or "UNKNOWN").upper().replace(" ","_"),"assumptions":assumptions,"evidence_quality":quality}

def estimate_from_profile(audience_profile:str,application_type:str):
    ap=audience_profile.upper(); ranges={"SMALL_LOCAL_AUDIENCE":((1000,5000),(10,40)),"GROWING_BUSINESS":((10000,30000),(50,200)),"NATIONAL_AUDIENCE":((50000,200000),(150,700)),"INTERNATIONAL_AUDIENCE":((100000,500000),(300,1500)),"LARGE_PUBLIC_PLATFORM":((500000,3000000),(1000,8000))}
    users,conc=ranges.get(ap,((10000,30000),(50,200)))
    return {"estimated_monthly_users":{"min":users[0],"max":users[1]},"estimated_concurrency":{"min":conc[0],"max":conc[1]},"confidence":"LOW","assumptions":[f"Estimate based on {audience_profile} and {application_type}; replace with measured data when available."]}
