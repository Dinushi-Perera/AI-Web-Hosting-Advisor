def build_architecture(recommended:str,payload:dict):
    nodes=[{"id":"users","type":"CLIENT","label":"Users"},{"id":"cdn","type":"CDN","label":"CDN / Edge"},{"id":"app","type":"COMPUTE","label":{"VPS":"VPS Application Server","CLOUD_VM":"Cloud VM Application Tier","KUBERNETES":"Kubernetes Workloads"}.get(recommended,recommended)},{"id":"db","type":"DATABASE","label":"Managed Database" if str(payload.get("managedDatabase") or payload.get("managed_database") or "").lower() in {"true","yes"} else "Database"},{"id":"monitoring","type":"MONITORING","label":"Monitoring"}]
    edges=[{"source":"users","target":"cdn"},{"source":"cdn","target":"app"},{"source":"app","target":"db"},{"source":"app","target":"monitoring"}]
    return {"nodes":nodes,"edges":edges}
