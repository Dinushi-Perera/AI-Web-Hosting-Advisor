from __future__ import annotations
from app.core.exceptions import AppError

def _metric(data:dict,name:str)->dict:
    metrics=data.get("metrics") or {}
    metric=next((item for item in metrics if isinstance(item,dict) and item.get("name")==name),None) if isinstance(metrics,list) else metrics.get(name)
    if not isinstance(metric,dict):return {}
    values=metric.get("values",metric)
    return values if isinstance(values,dict) else {}

def _n(values:dict,*keys):
    for key in keys:
        if key in values:
            try:return float(values[key])
            except (TypeError,ValueError):pass
    return None

def _checks(data:dict,normalized:dict)->tuple[int,int]:
    legacy=_metric(normalized,"checks")
    if legacy:
        return int(_n(legacy,"passes") or 0),int(_n(legacy,"fails") or 0)
    results=data.get("results")
    section=results.get("checks") if isinstance(results,dict) else None
    if not isinstance(section,dict):return 0,0
    check_metrics={**normalized,"metrics":section.get("metrics") or []}
    succeeded=_metric(check_metrics,"checks_succeeded");failed=_metric(check_metrics,"checks_failed")
    passes=int(_n(succeeded,"matches") or 0);fails=int(_n(failed,"matches") or 0)
    if passes or fails:return passes,fails
    rows=section.get("results") or []
    return sum(int(_n(row,"passes") or 0) for row in rows if isinstance(row,dict)),sum(int(_n(row,"fails") or 0) for row in rows if isinstance(row,dict))

def parse_summary(data:dict)->dict:
    if not isinstance(data,dict):raise AppError("INVALID_K6_RESULT","The uploaded JSON is not a supported k6 summary export.",422)
    metrics=data.get("metrics");results=data.get("results")
    if metrics is None and isinstance(results,dict):metrics=results.get("metrics")
    if not isinstance(metrics,(dict,list)):raise AppError("INVALID_K6_RESULT","The uploaded JSON is not a supported k6 summary export.",422)
    normalized={**data,"metrics":metrics}
    duration=_metric(normalized,"http_req_duration");failed=_metric(normalized,"http_req_failed");requests=_metric(normalized,"http_reqs");iterations=_metric(normalized,"iterations");vus=_metric(normalized,"vus_max")
    p95=_n(duration,"p(95)","p95")
    failed_rate=_n(failed,"rate","value");passes,fails=_checks(data,normalized)
    if p95 is None or failed_rate is None or passes+fails==0:raise AppError("INVALID_K6_RESULT","Required k6 p95, failure-rate, and check metrics are missing.",422)
    request_count=int(_n(requests,"count") or 0);average_rps=_n(requests,"rate")
    config=data.get("config") or {};elapsed=_n(config,"duration") if isinstance(config,dict) else None
    if average_rps is None and elapsed and elapsed>0:average_rps=request_count/elapsed
    return {"total_requests":request_count,"total_iterations":int(_n(iterations,"count") or 0),"average_rps":average_rps,"http_req_duration_avg_ms":_n(duration,"avg"),"http_req_duration_min_ms":_n(duration,"min"),"http_req_duration_max_ms":_n(duration,"max"),"http_req_duration_p50_ms":_n(duration,"med","p(50)","p50"),"http_req_duration_p90_ms":_n(duration,"p(90)","p90"),"http_req_duration_p95_ms":p95,"http_req_duration_p99_ms":_n(duration,"p(99)","p99"),"http_req_failed_rate":failed_rate,"checks_passed":passes,"checks_failed":fails,"data_received_bytes":int(_n(_metric(normalized,"data_received"),"count") or 0),"data_sent_bytes":int(_n(_metric(normalized,"data_sent"),"count") or 0),"peak_vus":int(_n(vus,"max","value") or 0)}
