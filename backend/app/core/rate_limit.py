import time
from collections import defaultdict,deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
LIMITS={"/api/v1/auth/login":(5,60),"/api/v1/auth/register":(3,60),"/api/v1/analysis/check-url":(20,60),"/api/v1/analysis/check-website":(20,60)}
class RateLimitMiddleware(BaseHTTPMiddleware):
    buckets=defaultdict(deque)
    async def dispatch(self,request,call_next):
        cfg=LIMITS.get(request.url.path)
        if cfg:
            limit,window=cfg; key=f"{request.client.host if request.client else 'unknown'}:{request.url.path}"; now=time.time(); q=self.buckets[key]
            while q and q[0]<=now-window:q.popleft()
            if len(q)>=limit:return JSONResponse(status_code=429,content={"success":False,"message":"Too many requests. Try again later.","code":"RATE_LIMITED","data":None,"error":{"code":"RATE_LIMITED"}})
            q.append(now)
        return await call_next(request)
