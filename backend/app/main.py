import time,uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import Counter,Histogram,generate_latest,CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.core.config import settings
from app.core.database import Base,engine
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.health import readiness
from app.api.v1 import auth,users,projects,analysis,technology,performance,workload,load_tests,recommendations,pricing,optimizations,reports,notifications,feedback,dashboard,tests_dashboard
REQUESTS=Counter("hosting_advisor_http_requests_total","HTTP requests",["method","path","status"])
LATENCY=Histogram("hosting_advisor_http_request_duration_seconds","HTTP latency",["method","path"])
@asynccontextmanager
async def lifespan(app:FastAPI):
    configure_logging();settings.ensure_storage()
    # The built-in SQLite URL is the zero-configuration development fallback.
    # Initialize it automatically so a fresh local start cannot accept requests
    # against an empty database. MySQL and production still require migrations.
    is_sqlite_development=(settings.app_env.lower()=="development" and settings.database_url.startswith("sqlite"))
    if settings.auto_create_tables or is_sqlite_development:Base.metadata.create_all(engine)
    yield
app=FastAPI(title=settings.app_name,version="1.0.0",default_response_class=ORJSONResponse,lifespan=lifespan,description="Production-oriented FastAPI backend for the AI-Driven Web Hosting Advisor. All monetary API outputs are USD.")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Request-ID"])
app.add_middleware(RateLimitMiddleware)
@app.middleware("http")
async def request_middleware(request:Request,call_next):
    rid=request.headers.get("X-Request-ID") or str(uuid.uuid4());request.state.request_id=rid;start=time.perf_counter()
    cl=request.headers.get("content-length")
    try:
        if cl and int(cl)>12_000_000:
            return ORJSONResponse(status_code=413,content={"success":False,"message":"Request body is too large.","code":"REQUEST_TOO_LARGE","error":{"code":"REQUEST_TOO_LARGE"},"requestId":rid})
    except ValueError:
        return ORJSONResponse(status_code=400,content={"success":False,"message":"Invalid Content-Length header.","code":"BAD_REQUEST","error":{"code":"BAD_REQUEST"},"requestId":rid})
    response=await call_next(request);duration=time.perf_counter()-start;response.headers["X-Request-ID"]=rid;response.headers["X-Content-Type-Options"]="nosniff";response.headers["Referrer-Policy"]="no-referrer";response.headers["Permissions-Policy"]="geolocation=(), microphone=(), camera=()"
    if settings.app_env=="production" and settings.cookie_secure:response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
    route=getattr(request.scope.get("route"),"path",request.url.path)
    REQUESTS.labels(request.method,route,response.status_code).inc();LATENCY.labels(request.method,route).observe(duration);return response
@app.exception_handler(AppError)
async def app_error(request:Request,exc:AppError):return ORJSONResponse(status_code=exc.status_code,content={"success":False,"message":exc.message,"code":exc.code,"data":None,"error":{"code":exc.code,"details":exc.details},"requestId":getattr(request.state,"request_id",None)})
@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):return ORJSONResponse(status_code=422,content={"success":False,"message":"Validation failed.","code":"VALIDATION_ERROR","data":None,"error":{"code":"VALIDATION_ERROR","details":exc.errors()},"requestId":getattr(request.state,"request_id",None)})
@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):return ORJSONResponse(status_code=500,content={"success":False,"message":"An internal error occurred.","code":"INTERNAL_ERROR","data":None,"error":{"code":"INTERNAL_ERROR"},"requestId":getattr(request.state,"request_id",None)})
@app.get("/health",tags=["Health"])
def health():return {"status":"ok","service":settings.app_name}
@app.get("/health/ready",tags=["Health"])
def ready():
    r=readiness();return ORJSONResponse(status_code=200 if r["ready"] else 503,content=r)
@app.get("/metrics",include_in_schema=False)
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
for router in [auth.router,users.router,projects.router,analysis.router,technology.router,performance.router,workload.router,load_tests.router,recommendations.router,pricing.router,optimizations.router,reports.router,notifications.router,feedback.router,dashboard.router,tests_dashboard.router]:app.include_router(router,prefix=settings.api_v1_prefix)
