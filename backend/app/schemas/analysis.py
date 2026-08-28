from pydantic import BaseModel, Field, HttpUrl
class URLCheckRequest(BaseModel): url: str
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
