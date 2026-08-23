from pydantic import BaseModel, EmailStr, Field, field_validator
class UserPatch(BaseModel):
    fullName: str | None = Field(default=None,min_length=2,max_length=120)
    email: EmailStr | None = None
    experienceLevel: str | None = None
    defaultRegion: str | None = None
    timezone: str | None = None
    currency: str | None = None
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v is not None and v.upper()!="USD": raise ValueError("Only USD is supported")
        return "USD" if v else v
    @field_validator("experienceLevel")
    @classmethod
    def experience(cls,v):
        if v is not None and v.upper() not in {"BEGINNER","INTERMEDIATE","ADVANCED"}: raise ValueError("Invalid experience level")
        return v
class PreferencePatch(BaseModel):
    theme: str | None = None
    defaultCurrency: str | None = None
    defaultRegion: str | None = None
    timezone: str | None = None
    chartAnimations: bool | None = None
    emailNotifications: bool | None = None
    analysisNotifications: bool | None = None
    onboardingCompleted: bool | None = None
    @field_validator("defaultCurrency")
    @classmethod
    def usd(cls,v):
        if v is not None and v.upper()!="USD": raise ValueError("Only USD is supported")
        return "USD" if v else v
