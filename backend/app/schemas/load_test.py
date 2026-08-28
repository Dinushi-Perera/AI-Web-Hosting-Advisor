from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from urllib.parse import unquote
from app.utils.enums import LoadTestType

class LoadTestEnvironmentInput(BaseModel):
    hosting_type: str | None = Field(default=None,max_length=40)
    vcpu: int | None = Field(default=None,ge=1,le=1024)
    ram_gb: float | None = Field(default=None,gt=0,le=16384)
    database_type: str | None = Field(default=None,max_length=80)
    cdn_enabled: bool | None = None
    notes: str | None = Field(default=None,max_length=1000)

class LoadTestResourceMetricsInput(BaseModel):
    cpu_peak_percent: float | None = Field(default=None,ge=0,le=100)
    cpu_avg_percent: float | None = Field(default=None,ge=0,le=100)
    ram_peak_percent: float | None = Field(default=None,ge=0,le=100)
    ram_avg_percent: float | None = Field(default=None,ge=0,le=100)
    database_cpu_peak_percent: float | None = Field(default=None,ge=0,le=100)
    database_connections_peak: int | None = Field(default=None,ge=0)
    server_load_average: float | None = Field(default=None,ge=0)
    notes: str | None = Field(default=None,max_length=1000)

class LoadTestPlanCreate(BaseModel):
    authorization_confirmed: bool
    risk_acknowledged: bool
    test_type: LoadTestType = LoadTestType.LOAD
    target_url: str = Field(min_length=8,max_length=2048)
    target_virtual_users: int | None = Field(default=None,ge=1)
    virtual_users: int | None = Field(default=None,ge=1)
    duration_seconds: int | None = Field(default=None,ge=1)
    response_time_threshold_ms: int = Field(default=2000,gt=0,le=60000)
    error_rate_threshold: float = Field(default=0.01,ge=0,le=1)
    think_time_min_seconds: int = Field(default=1,ge=0,le=60)
    think_time_max_seconds: int = Field(default=3,ge=0,le=60)
    safe_paths: list[str] = Field(default_factory=lambda:["/"],max_length=10)
    environment: LoadTestEnvironmentInput | None = None

    @model_validator(mode="after")
    def validate_think_time(self):
        if self.think_time_min_seconds>self.think_time_max_seconds:raise ValueError("Think-time minimum cannot exceed the maximum.")
        return self

    @field_validator("safe_paths")
    @classmethod
    def validate_paths(cls,paths:list[str]):
        blocked=("/admin","/delete","/pay","/checkout/confirm","/password-reset","/delete-account","/upload-large-file")
        clean=[]
        for path in paths:
            decoded=path
            for _ in range(3):decoded=unquote(decoded)
            decoded=decoded.lower();segments=decoded.split("/")
            if not decoded.startswith("/") or decoded.startswith("//") or "\\" in decoded or "?" in decoded or "#" in decoded or "\x00" in decoded or any(x in {".",".."} for x in segments) or any(x in decoded for x in blocked):
                raise ValueError("Only confirmed, safe GET paths beginning with / are allowed.")
            clean.append(path[:500])
        return clean or ["/"]

class LoadTestStageRead(BaseModel):
    stage_order: int
    duration_seconds: int
    target_virtual_users: int
    stage_type: str

class LoadTestResultRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    public_id: str
    overall_status: str
    ai_validation_status: str
    peak_vus: int | None
    average_rps: float | None
    http_req_duration_avg_ms: float | None
    http_req_duration_p95_ms: float | None
    http_req_duration_p99_ms: float | None
    http_req_failed_rate: float | None
    checks_passed: int | None
    checks_failed: int | None
    thresholds_passed: bool
    analysis_json: dict
    created_at: datetime

class LoadTestRecommendationRead(BaseModel):
    recommended_test_type: str
    reason: str
    expected_concurrent_users: int
    requests_per_user_per_minute: float
    estimated_rps: float
    peak_rps: float
    traffic_classification: str
    recommended_target_vus: int
    recommended_duration_seconds: int
    thresholds: dict
    ai_context: dict
    calculation: dict
    warnings: list[str]
