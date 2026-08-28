import hashlib,json
import httpx
from app.core.config import settings

THRESHOLDS={"LCP":(2500,4000),"INP":(200,500),"CLS":(.1,.25),"FCP":(1800,3000),"TBT":(200,600),"SPEED_INDEX":(3400,5800)}
FIELD_KEYS={"lcp_ms":["LARGEST_CONTENTFUL_PAINT_MS"],"inp_ms":["INTERACTION_TO_NEXT_PAINT","EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT"],"cls":["CUMULATIVE_LAYOUT_SHIFT_SCORE"]}

def metric_status(name:str,value):
    if value is None:return "UNKNOWN"
    good,poor=THRESHOLDS.get(name,(None,None))
    if good is None:return "UNKNOWN"
    return "GOOD" if value<=good else "NEEDS_IMPROVEMENT" if value<=poor else "POOR"

def score_status(value):
    if value is None:return "UNKNOWN"
    return "GOOD" if value>=90 else "NEEDS_IMPROVEMENT" if value>=50 else "POOR"

def _field_metric(experience:dict,aliases:list[str],cls=False):
    metrics=(experience or {}).get("metrics") or {};row=next((metrics[key] for key in aliases if key in metrics),None)
    if not row:return None
    percentile=row.get("percentile");value=float(percentile)/100 if cls and percentile is not None and float(percentile)>1 else percentile
    category={"FAST":"GOOD","AVERAGE":"NEEDS_IMPROVEMENT","SLOW":"POOR"}.get(str(row.get("category") or "").upper(),"UNKNOWN")
    return {"value":value,"category":category,"percentile":75,"distributions":row.get("distributions") or []}

def _field_data(data:dict):
    def extract(experience):return {name:item for name,aliases in FIELD_KEYS.items() if (item:=_field_metric(experience,aliases,name=="cls"))}
    return {"page":{"id":(data.get("loadingExperience") or {}).get("id"),"overall_category":(data.get("loadingExperience") or {}).get("overall_category"),"metrics":extract(data.get("loadingExperience") or {})},"origin":{"id":(data.get("originLoadingExperience") or {}).get("id"),"overall_category":(data.get("originLoadingExperience") or {}).get("overall_category"),"metrics":extract(data.get("originLoadingExperience") or {})}}

def _opportunities(audits:dict):
    rows=[]
    for audit_id,audit in audits.items():
        details=audit.get("details") or {};saving_ms=details.get("overallSavingsMs") or 0;saving_bytes=details.get("overallSavingsBytes") or 0
        if audit.get("scoreDisplayMode") in {"notApplicable","informative","manual"} or (not saving_ms and not saving_bytes):continue
        rows.append({"id":audit_id,"title":audit.get("title") or audit_id,"description":audit.get("description"),"score":audit.get("score"),"display_value":audit.get("displayValue"),"savings_ms":round(float(saving_ms),1),"savings_bytes":round(float(saving_bytes),1)})
    return sorted(rows,key=lambda row:(row["savings_ms"],row["savings_bytes"]),reverse=True)[:10]

def _audit_from_lighthouse(data:dict,strategy:str):
    lighthouse=data.get("lighthouseResult") or {};categories=lighthouse.get("categories") or {};audits=lighthouse.get("audits") or {}
    def score(key):
        value=(categories.get(key) or {}).get("score");return round(value*100) if isinstance(value,(int,float)) else None
    def numeric(key):return (audits.get(key) or {}).get("numericValue")
    lab={"lcp_ms":numeric("largest-contentful-paint"),"inp_ms":numeric("interaction-to-next-paint"),"cls":numeric("cumulative-layout-shift"),"fcp_ms":numeric("first-contentful-paint"),"tbt_ms":numeric("total-blocking-time"),"speed_index_ms":numeric("speed-index")}
    field=_field_data(data);selected={};sources={}
    for metric in ("lcp_ms","inp_ms","cls"):
        page=(field["page"]["metrics"].get(metric) or {}).get("value");origin=(field["origin"]["metrics"].get(metric) or {}).get("value")
        if page is not None:selected[metric]=page;sources[metric]="CRUX_PAGE_FIELD"
        elif origin is not None:selected[metric]=origin;sources[metric]="CRUX_ORIGIN_FIELD"
        elif lab.get(metric) is not None:selected[metric]=lab[metric];sources[metric]="LIGHTHOUSE_LAB"
        else:selected[metric]=None;sources[metric]="UNAVAILABLE"
    metrics={**lab,**selected,"fcp_ms":lab["fcp_ms"],"tbt_ms":lab["tbt_ms"],"speed_index_ms":lab["speed_index_ms"]}
    statuses={"lcp":metric_status("LCP",metrics["lcp_ms"]),"inp":metric_status("INP",metrics["inp_ms"]),"cls":metric_status("CLS",metrics["cls"]),"fcp":metric_status("FCP",metrics["fcp_ms"]),"tbt":metric_status("TBT",metrics["tbt_ms"]),"speedIndex":metric_status("SPEED_INDEX",metrics["speed_index_ms"])}
    cwv=[statuses[name] for name in ("lcp","inp","cls")];overall="PASSED" if all(value=="GOOD" for value in cwv) else "FAILED" if all(value!="UNKNOWN" for value in cwv) else "INSUFFICIENT_DATA"
    category_scores={key:score(key) for key in ("performance","accessibility","best-practices","seo")}
    metrics.update({"statuses":statuses,"metric_sources":sources,"lab_metrics":lab,"field_data":field,"core_web_vitals":{"overall_status":overall,"required_metrics":["LCP","INP","CLS"],"percentile":75,"statuses":{"LCP":statuses["lcp"],"INP":statuses["inp"],"CLS":statuses["cls"]}},"lighthouse":{"version":lighthouse.get("lighthouseVersion"),"fetch_time":lighthouse.get("fetchTime"),"requested_url":lighthouse.get("requestedUrl"),"final_url":lighthouse.get("finalUrl"),"category_statuses":{name:score_status(value) for name,value in category_scores.items()}},"opportunities":_opportunities(audits)})
    warning=None if overall!="INSUFFICIENT_DATA" else "Core Web Vitals field data is incomplete; Lighthouse lab evidence is shown separately and confidence is reduced."
    return {"strategy":strategy.upper(),"status":"AVAILABLE","performance_score":category_scores["performance"],"accessibility_score":category_scores["accessibility"],"best_practices_score":category_scores["best-practices"],"seo_score":category_scores["seo"],"metrics":metrics,"statuses":statuses,"warning":warning,"source":"PageSpeed Insights + Lighthouse + CrUX"}

def _unavailable(strategy,message):return {"strategy":strategy.upper(),"status":"UNAVAILABLE","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":{"core_web_vitals":{"overall_status":"INSUFFICIENT_DATA"},"lab_metrics":{},"field_data":{}},"statuses":{},"warning":message,"source":"PageSpeed Insights"}

def _cache_get(key:str):
    try:
        import redis
        raw=redis.from_url(settings.redis_url,socket_connect_timeout=.5,socket_timeout=.5).get(key);return json.loads(raw) if raw else None
    except Exception:return None

def _cache_set(key:str,value:dict):
    try:
        import redis
        redis.from_url(settings.redis_url,socket_connect_timeout=.5,socket_timeout=.5).setex(key,settings.pagespeed_cache_seconds,json.dumps(value))
    except Exception:pass

def audit_pagespeed(url:str,strategy:str):
    key="pagespeed:"+hashlib.sha256(f"{url}|{strategy}".encode()).hexdigest();cached=_cache_get(key)
    if cached:cached["cache_status"]="HIT";return cached
    if not settings.pagespeed_api_key:return _unavailable(strategy,"PageSpeed API key is not configured; no live performance result is claimed.")
    params={"url":url,"strategy":strategy,"key":settings.pagespeed_api_key,"category":["performance","accessibility","best-practices","seo"]}
    try:
        response=httpx.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed",params=params,timeout=45.0);response.raise_for_status();result=_audit_from_lighthouse(response.json(),strategy);result["cache_status"]="MISS";_cache_set(key,result);return result
    except (httpx.HTTPError,ValueError,KeyError,TypeError):return _unavailable(strategy,"PageSpeed Insights was unavailable or returned invalid evidence; recommendation confidence was reduced.")

def audit(url:str):return [audit_pagespeed(url,"mobile"),audit_pagespeed(url,"desktop")]

def planned_budget(payload:dict,mode:str):
    """Return launch targets for non-live projects without pretending they are measurements."""
    media=str(payload.get("mediaUsage") or payload.get("features") or "").lower();traffic=str(payload.get("traffic") or payload.get("audience") or payload.get("growth") or "").lower()
    common={"target_lcp_ms":2500,"target_inp_ms":200,"target_cls":.1,"initial_js_kb":220 if "video" in media or "stream" in media else 180,"largest_image_kb":350 if "e-commerce" in str(payload.get("websiteType") or payload.get("industry") or "").lower() else 250,"api_p95_ms":350 if "large" in traffic or "international" in traffic else 500,"target_error_rate":.01,"evidence":"DESIGN_TARGET","core_web_vitals":{"overall_status":"PLANNED","required_metrics":["LCP","INP","CLS"],"percentile":75}}
    warning=f"{mode.replace('_',' ').title()} has no live measurements yet. These are launch performance budgets, not observed results."
    return [{"strategy":strategy,"status":"PLANNED","performance_score":None,"accessibility_score":None,"best_practices_score":None,"seo_score":None,"metrics":common,"statuses":{},"warning":warning,"source":"Design performance budget"} for strategy in ("MOBILE","DESKTOP")]
