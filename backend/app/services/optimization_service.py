def generate(performance:list[dict], technologies:list[dict], workload:dict, recommendation:str)->list[dict]:
    out=[]
    mobile=next((p for p in performance if p.get("strategy")=="MOBILE"),{})
    m=mobile.get("metrics") or {}
    if m.get("lcp_ms") and m["lcp_ms"]>2500:
        out.append({"priority":"HIGH","category":"FRONTEND","title":"Optimize Largest Contentful Paint","explanation":"Reduce the size and delivery time of the largest above-the-fold resource before increasing infrastructure.","impact":"Performance","difficulty":"EASY","benefit":"Improve LCP and perceived load speed","steps":["Compress and resize hero media","Preload only the critical LCP asset","Review server response and render blocking resources"]})
    cdn=any(t.get("category")=="CDN" and t.get("confidence",0)>=0.6 for t in technologies)
    if not cdn:
        out.append({"priority":"MEDIUM","category":"CACHE_CDN","title":"Add an edge CDN for public assets","explanation":"No reliable CDN evidence was detected. Edge caching can reduce origin load and latency for geographically distributed users.","impact":"Performance + origin load","difficulty":"MEDIUM","benefit":"Lower latency and bandwidth pressure","steps":["Cache versioned static assets","Set safe cache headers","Measure cache hit ratio"]})
    if str(workload.get("database_intensity")) in {"HIGH","VERY_HIGH"}:
        out.append({"priority":"HIGH","category":"DATABASE","title":"Profile database hot paths","explanation":"The declared database workload is high, so query and index efficiency should be validated before adding compute.","impact":"Backend latency","difficulty":"MEDIUM","benefit":"Reduce database CPU and response time","steps":["Capture slow queries","Review indexes","Measure before and after"]})
    out.append({"priority":"MEDIUM","category":"MONITORING","title":"Monitor latency, errors and saturation","explanation":"Use application and infrastructure metrics so future sizing is based on measured demand instead of assumptions.","impact":"Reliability","difficulty":"EASY","benefit":"Faster diagnosis and better future recommendations","steps":["Track p95 latency","Track 5xx/error rate","Track CPU, memory and database saturation"]})
    if recommendation=="KUBERNETES": out.append({"priority":"HIGH","category":"SCALABILITY","title":"Define Kubernetes operational guardrails","explanation":"Kubernetes should be introduced with resource limits, autoscaling policy, observability and rollback procedures.","impact":"Reliability + operations","difficulty":"HARD","benefit":"Reduce orchestration risk","steps":["Set requests/limits","Configure HPA carefully","Add deployment health checks and rollback"]})
    return out
