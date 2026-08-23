from sqlalchemy import text,select
from app.core.database import SessionLocal
from app.models import MLModelVersion
from app.core.config import settings
def readiness():
    result={"database":"down","redis":"down","active_model":None}
    try:
        db=SessionLocal();db.execute(text("SELECT 1"));result["database"]="ok";m=db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)));result["active_model"]=m.version if m else None;db.close()
    except Exception:pass
    try:
        import redis;r=redis.from_url(settings.redis_url,socket_connect_timeout=1,socket_timeout=1);r.ping();result["redis"]="ok"
    except Exception:pass
    result["ready"]=result["database"]=="ok" and result["redis"]=="ok"
    return result
