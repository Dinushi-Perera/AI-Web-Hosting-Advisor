import httpx, hashlib, json
from app.core.config import settings

def metric_status(name:str,value):
    if value is None: return "UNKNOWN"
    thresholds={"LCP":(2500,4000),"INP":(200,500),"CLS":(0.1,0.25),"FCP":(1800,3000),"TBT":(200,600),"SPEED_INDEX":(3400,5800)}
    good,poor=thresholds.get(name,(None,None))
    if good is None: return "UNKNOWN"
    return "GOOD" if value<=good else "NEEDS_IMPROVEMENT" if value<=poor else "POOR"

def _audit_from_lighthouse(data:dict,strategy:str):
    lr=data.get("lighthouseResult",{}); cats=lr.get("categories",{}); audits=lr.get("audits",{})
    def score(k):
        v=cats.get(k,{}).get("score"); return round(v*100) if isinstance(v,(int,float)) else None
    def num(k): return audits.get(k,{}).get("numericValue")
    metrics={"lcp_ms":num("largest-contentful-paint"),"inp_ms":num("interaction-to-next-paint"),"cls":audits.get("cumulative-layout-shift",{}).get("numericValue"),"fcp_ms":num("first-contentful-paint"),"tbt_ms":num("total-blocking-time"),"speed_index_ms":num("speed-index")}
    statuses={"lcp":metric_status("LCP",metrics["lcp_ms"]),"inp":metric_status("INP",metrics["inp_ms"]),"cls":metric_status("CLS",metrics["cls"]),"fcp":metric_status("FCP",metrics["fcp_ms"]),"tbt":metric_status("TBT",metrics["tbt_ms"]),"speedIndex":metric_status("SPEED_INDEX",metrics["speed_index_ms"])}
    return {"strategy":strategy.upper(),"status":"AVAILABLE","performance_score":score("performance"),"accessibility_score":score("accessibility"),"best_practices_score":score("best-practices"),"seo_score":score("seo"),"metrics":metrics,"statuses":statuses,"warning":None}

def _cache_get(key:str):
    try:
        import redis
        r=redis.from_url(settings.redis_url,socket_connect_timeout=0.5,socket_timeout=0.5)
        raw=r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None

def _cache_set(key:str,value:dict):
    try:
        import redis
        r=redis.from_url(settings.redis_url,socket_connect_timeout=0.5,socket_timeout=0.5)
        r.setex(key,settings.pagespeed_cache_seconds,json.dumps(value))
    except Exception:
        pass

def audit_pagespeed(url:str,strategy:str):
    key="pagespeed:"+hashlib.sha256(f"{url}|{strategy}".encode()).hexdigest()
    cached=_cache_get(key)
    if cached:
        cached["cache_status"]="HIT"
        return cached
    if not settings.pagespeed_api_key:
        return {"strategy":strategy.upper(),"status":"UNAVAILABLE","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":{},"statuses":{},"warning":"PageSpeed API key is not configured; performance evidence is unavailable."}
    params={"url":url,"strategy":strategy,"key":settings.pagespeed_api_key,"category":["performance","accessibility","best-practices","seo"]}
    try:
        r=httpx.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed",params=params,timeout=30.0)
        r.raise_for_status(); result=_audit_from_lighthouse(r.json(),strategy); result["cache_status"]="MISS"; _cache_set(key,result); return result
    except Exception:
        return {"strategy":strategy.upper(),"status":"UNAVAILABLE","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":{},"statuses":{},"warning":"PageSpeed Insights was unavailable; recommendation confidence was reduced."}

def audit(url:str): return [audit_pagespeed(url,"mobile"),audit_pagespeed(url,"desktop")]
