def analyse(metrics:dict,p95_threshold:float,error_threshold:float,environment:dict|None=None,predicted:dict|None=None,target_vus:int|None=None,resource_metrics:dict|None=None,expected_rps:float|None=None,peak_rps:float|None=None)->dict:
    p95_ok=float(metrics["http_req_duration_p95_ms"])<=p95_threshold
    error_ok=float(metrics["http_req_failed_rate"])<=error_threshold
    checks_ok=(metrics.get("checks_failed") or 0)==0
    overall="PASS" if p95_ok and error_ok and checks_ok else "PARTIAL_PASS" if sum((p95_ok,error_ok,checks_ok))>=2 else "FAIL"
    environment=environment or {};predicted=predicted or {};resource_metrics=resource_metrics or {}
    resources_known=bool(environment.get("vcpu") and environment.get("ram_gb"));resource_match=resources_known and environment.get("vcpu")==predicted.get("vcpu") and float(environment.get("ram_gb"))==float(predicted.get("ram_gb") or -1)
    workload_reached=not target_vus or int(metrics.get("peak_vus") or 0)>=target_vus
    actual_rps=float(metrics.get("average_rps") or 0);coverage_ratio=None if not expected_rps else actual_rps/float(expected_rps)
    traffic_coverage="INSUFFICIENT_EVIDENCE" if coverage_ratio is None else "UNDER_TARGET" if coverage_ratio<.75 else "NEAR_EXPECTED" if coverage_ratio<.95 else "MEETS_EXPECTED" if coverage_ratio<=1.10 else "EXCEEDS_EXPECTED"
    if not resource_match or not workload_reached:validation="INSUFFICIENT_EVIDENCE"
    elif overall=="PASS":validation="SUPPORTED"
    elif overall=="PARTIAL_PASS":validation="PARTIALLY_SUPPORTED"
    else:validation="NOT_SUPPORTED"
    reasons=[]
    if not p95_ok:reasons.append(f"p95 response time {metrics['http_req_duration_p95_ms']:.0f} ms exceeded the {p95_threshold:.0f} ms threshold.")
    if not error_ok:reasons.append(f"Request failure rate {metrics['http_req_failed_rate']:.2%} exceeded the {error_threshold:.2%} threshold.")
    if not checks_ok:reasons.append("One or more configured functional checks failed.")
    if not resources_known:reasons.append("The website result is valid, but tested CPU/RAM was not provided, so resource sizing cannot be directly validated.")
    elif not resource_match:reasons.append("The tested CPU/RAM does not match the predicted starting size, so this run cannot directly validate the resource-size prediction.")
    if not workload_reached:reasons.append(f"The test reached {metrics.get('peak_vus') or 0} VUs, below the planned target of {target_vus}; workload evidence is incomplete.")
    if traffic_coverage=="UNDER_TARGET":reasons.append(f"Average throughput reached {actual_rps:.2f} RPS, below 75% of the expected {expected_rps:.2f} RPS workload.")
    if not p95_ok and resource_metrics.get("cpu_peak_percent",0)>=90:reasons.append("CPU capacity may be a contributing factor because measured peak CPU was at least 90%.")
    if not p95_ok and resource_metrics.get("database_connections_peak") and resource_metrics.get("cpu_peak_percent",0)<60:reasons.append("The database or connection pool may be a contributing constraint; confirm configured connection limits before changing CPU/RAM sizing.")
    return {"overall_status":overall,"ai_validation_status":validation,"thresholds":{"p95":{"passed":p95_ok,"limit_ms":p95_threshold,"actual_ms":metrics["http_req_duration_p95_ms"]},"error_rate":{"passed":error_ok,"limit":error_threshold,"actual":metrics["http_req_failed_rate"]},"checks":{"passed":checks_ok}},"environment_matches_prediction":resource_match,"planned_workload_reached":workload_reached,"traffic_coverage":{"status":traffic_coverage,"actual_rps":actual_rps,"expected_rps":expected_rps,"peak_rps":peak_rps,"ratio":None if coverage_ratio is None else round(coverage_ratio,3)},"reasons":reasons,"resource_metrics":resource_metrics,"evidence_note":"A k6 result is scenario-specific. Application code, database, network, cache, CDN, dependencies, and server configuration can all affect it."}
