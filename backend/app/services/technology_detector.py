import re
from bs4 import BeautifulSoup
from app.services.url_security_service import safe_fetch

SENSITIVE_HEADERS={"set-cookie","authorization","proxy-authorization"}

def _add(out,category,technology,weight,source,pattern):
    key=(category,technology)
    item=out.setdefault(key,{"category":category,"technology":technology,"score":0.0,"evidence":[]})
    item["score"]+=weight
    item["evidence"].append({"source":source,"pattern":pattern,"weight":weight})

def detect_from_response(response:dict)->list[dict]:
    headers={k.lower():v for k,v in response.get("headers",{}).items() if k.lower() not in SENSITIVE_HEADERS}
    html=response.get("content",b"").decode("utf-8",errors="ignore")[:2_000_000]
    low=html.lower(); out={}
    if "wp-content" in low: _add(out,"CMS","WordPress",0.45,"HTML","wp-content")
    if "wp-includes" in low: _add(out,"CMS","WordPress",0.35,"HTML","wp-includes")
    if "__next_data__" in low: _add(out,"FRONTEND","Next.js",0.5,"HTML","__NEXT_DATA__")
    if "/_next/static/" in low: _add(out,"FRONTEND","Next.js",0.45,"HTML","/_next/static/")
    if "_nuxt/" in low: _add(out,"FRONTEND","Nuxt",0.65,"HTML","/_nuxt/")
    if "ng-version=" in low: _add(out,"FRONTEND","Angular",0.75,"HTML","ng-version")
    if "data-reactroot" in low or "react-dom" in low: _add(out,"FRONTEND","React",0.55,"HTML","React signature")
    server=headers.get("server","").lower()
    if "nginx" in server: _add(out,"WEB_SERVER","nginx",0.9,"HEADER","server: nginx")
    if "apache" in server: _add(out,"WEB_SERVER","Apache",0.9,"HEADER","server: apache")
    if "cloudflare" in server or "cf-ray" in headers or "cf-cache-status" in headers: _add(out,"CDN","Cloudflare",0.9,"HEADER","Cloudflare headers")
    if "x-powered-by" in headers:
        val=headers["x-powered-by"].lower()
        if "express" in val: _add(out,"BACKEND","Express",0.8,"HEADER","x-powered-by: Express")
        elif "php" in val: _add(out,"BACKEND","PHP",0.75,"HEADER","x-powered-by: PHP")
    if "strict-transport-security" in headers: _add(out,"SECURITY","HSTS",0.9,"HEADER","strict-transport-security")
    if "googletagmanager.com/gtag" in low or "google-analytics.com" in low: _add(out,"ANALYTICS","Google Analytics",0.9,"HTML","Google Analytics script")
    try:
        soup=BeautifulSoup(html,"lxml")
        gen=soup.find("meta",attrs={"name":re.compile("^generator$",re.I)})
        if gen and gen.get("content"):
            content=str(gen.get("content"))[:100]
            if "wordpress" in content.lower(): _add(out,"CMS","WordPress",0.55,"META","generator=WordPress")
    except Exception: pass
    results=[]
    for item in out.values():
        c=min(0.99,item.pop("score")); label="HIGH" if c>=0.8 else "MEDIUM" if c>=0.6 else "LOW"
        results.append({**item,"confidence":round(c,2),"confidence_label":label})
    if not any(x["category"]=="CMS" for x in results): results.append({"category":"CMS","technology":"No reliable CMS detected","confidence":0.45,"confidence_label":"LOW","evidence":[{"source":"HTML","pattern":"No supported CMS signature found","weight":0.45}]})
    return sorted(results,key=lambda x:(x["category"],-x["confidence"]))

def detect_url(url:str): return detect_from_response(safe_fetch(url))
