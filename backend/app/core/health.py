from sqlalchemy import text,select
from app.core.database import SessionLocal
from app.models import MLModelVersion
from app.core.config import settings
from app.services.ml_service import bundled_model_status
from app.services.k6_execution_service import _binary
def readiness():
    result={"database":"down","redis":"down","active_model":None,"k6_planner":"ready","k6_engine":"down","hosting_model":"down","resource_model":"down"}
    try:
        db=SessionLocal();db.execute(text("SELECT 1"));result["database"]="ok";m=db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)));result["active_model"]=m.version if m else None;db.close()
    except Exception:pass
    if result["active_model"] is None:
        bundled=bundled_model_status()["classifier"]
        if bundled["available"]: result["active_model"]=bundled["version"]
    models=bundled_model_status();result["hosting_model"]="ready" if models["classifier"]["available"] else "down";result["resource_model"]="ready" if models["resource"]["available"] else "down"
    try:_binary();result["k6_engine"]="ready"
    except Exception:pass
    try:
        import redis;r=redis.from_url(settings.redis_url,socket_connect_timeout=1,socket_timeout=1);r.ping();result["redis"]="ok"
    except Exception:pass
    result["ready"]=result["database"]=="ok" and result["redis"]=="ok"
    return result
