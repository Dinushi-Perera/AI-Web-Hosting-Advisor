from pathlib import Path
from urllib.parse import urlsplit
from sqlalchemy.orm import Session
from app.models import LoadTestPlan, Project
from app.core.config import settings
from app.core.exceptions import AppError
from app.services.url_security_service import validate_public_url

def _stages(kind:str,vus:int,duration:int):
    if kind=="SMOKE": return [{"duration":"30s","target":min(5,vus)},{"duration":"30s","target":0}]
    if kind=="SPIKE": return [{"duration":"30s","target":max(1,vus//10)},{"duration":"15s","target":vus},{"duration":"45s","target":vus},{"duration":"30s","target":0}]
    if kind=="SOAK": return [{"duration":"1m","target":vus},{"duration":f"{max(1,duration//60)}m","target":vus},{"duration":"1m","target":0}]
    if kind=="STRESS": return [{"duration":"1m","target":max(1,vus//4)},{"duration":"1m","target":max(1,vus//2)},{"duration":"1m","target":vus},{"duration":"1m","target":0}]
    return [{"duration":"30s","target":max(1,vus//10)},{"duration":"1m","target":max(1,vus//2)},{"duration":f"{max(1,duration//60)}m","target":vus},{"duration":"30s","target":0}]

def generate(db:Session,project:Project,user_id:str,req):
    if not req.authorization_confirmed or not req.risk_acknowledged: raise AppError("LOAD_TEST_AUTH_REQUIRED","Authorization and risk acknowledgement are required.",422)
    if req.virtual_users>settings.max_load_test_vus or req.duration_seconds>settings.max_load_test_duration_seconds: raise AppError("LOAD_TEST_LIMIT_EXCEEDED","Requested load test exceeds the configured prototype safety limits.",422)
    target=validate_public_url(req.target_url)
    if project.website_url and urlsplit(target).hostname!=urlsplit(project.website_url).hostname: raise AppError("LOAD_TEST_DOMAIN_MISMATCH","The load-test target must match the project's authorized domain.",422)
    stages=_stages(req.test_type.value,req.virtual_users,req.duration_seconds)
    script="import http from 'k6/http';\nimport { check, sleep } from 'k6';\n\n"+f"export const options = {{ stages: {stages!r}.map(x => ({{duration:x.duration,target:x.target}})), thresholds: {{ http_req_failed: ['rate<{req.error_rate_threshold}'], http_req_duration: ['p(95)<{req.response_time_threshold_ms}'] }} }};\n\nexport default function () {{ const res=http.get(__ENV.TARGET_URL); check(res, {{ 'status is successful': r => r.status >= 200 && r.status < 400 }}); sleep(1); }}\n"
    script=script.replace("'duration'","duration").replace("'target'","target").replace("'",'"')
    row=LoadTestPlan(project_id=project.id,user_id=user_id,test_type=req.test_type.value,virtual_users=req.virtual_users,duration_seconds=req.duration_seconds,target_url=target,response_time_threshold_ms=req.response_time_threshold_ms,error_rate_threshold=req.error_rate_threshold,stages=stages,script=script,safety_notes=["Run only against systems you own or are explicitly authorized to test.","The backend generates a plan; it does not automatically execute load against public targets."])
    db.add(row); db.flush(); filename=f"{project.id}-{row.id}.js"; path=Path(settings.load_test_storage_dir)/filename; path.write_text(script,encoding="utf-8"); row.file_key=filename; db.commit()
    return {"plan_id":row.id,"script":script,"filename":f"{project.title.lower().replace(' ','-')}-load-test.js","stages":stages,"safety_notes":row.safety_notes}
