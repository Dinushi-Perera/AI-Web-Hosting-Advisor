from pydantic import BaseModel, Field, HttpUrl
from app.utils.enums import LoadTestType
class URLCheckRequest(BaseModel): url: str
class LoadTestPlanRequest(BaseModel):
    authorization_confirmed: bool
    risk_acknowledged: bool
    test_type: LoadTestType = LoadTestType.LOAD
    virtual_users: int = Field(ge=1)
    duration_seconds: int = Field(ge=1)
    target_url: str
    response_time_threshold_ms: int = Field(default=2000, ge=100, le=60000)
    error_rate_threshold: float = Field(default=0.01, ge=0, le=1)
class FeedbackRequest(BaseModel):
    clarity_rating: int = Field(ge=1,le=5)
    usefulness_rating: int = Field(ge=1,le=5)
    ease_of_use_rating: int = Field(ge=1,le=5)
    recommendation_trust_rating: int = Field(ge=1,le=5)
    comments: str | None = Field(default=None,max_length=4000)
class CorrectionRequest(BaseModel): actual_technology: str = Field(min_length=1,max_length=120); reason: str = Field(min_length=1,max_length=500)
class OptimizationStatusRequest(BaseModel): status: str
class PreferredOptionRequest(BaseModel): option: str
class WorkloadProfileRequest(BaseModel): audience_profile: str; application_type: str
class ClarificationAnswerRequest(BaseModel): answers: dict
