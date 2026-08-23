from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ProjectCreate(BaseModel):
    model_config=ConfigDict(extra="allow")
    mode: str
    title: str | None = None
    name: str | None = None
    projectName: str | None = None
    input: dict[str, Any] | None = None
    status: str = "DRAFT"
    currency: str = "USD"
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v.upper() != "USD": raise ValueError("Only USD is supported")
        return "USD"

class ProjectPatch(BaseModel):
    model_config=ConfigDict(extra="allow")
    title: str | None = None
    name: str | None = None
    status: str | None = None
    input: dict[str, Any] | None = None
    currency: str | None = None
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v is not None and v.upper() != "USD": raise ValueError("Only USD is supported")
        return "USD" if v else v

class LiveFrontendRequest(BaseModel):
    projectName: str = Field(min_length=2,max_length=120)
    websiteUrl: str
    category: str
    region: str
    monthlyVisitors: int = Field(ge=0,le=1_000_000_000)
    concurrentUsers: int = Field(ge=1,le=1_000_000)
    growth: str
    trafficPattern: str
    budget: float = Field(ge=0,le=1_000_000)
    currency: str = "USD"
    budgetFlexibility: str
    managesServers: bool
    highAvailability: bool
    rapidScaling: bool
    kubernetesSkill: bool
    managedDatabase: bool
    backups: bool
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v.upper() != "USD": raise ValueError("Only USD is supported by this Sri Lankan project deployment")
        return "USD"

class PlannedFrontendRequest(BaseModel):
    model_config=ConfigDict(extra="allow")
    projectName: str = Field(min_length=2,max_length=120)
    currency: str = "USD"
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v.upper() != "USD": raise ValueError("Only USD is supported")
        return "USD"

class IdeaFrontendRequest(BaseModel):
    model_config=ConfigDict(extra="allow")
    projectName: str | None = None
    idea: str | None = None
    description: str | None = None
    currency: str = "USD"
    @field_validator("currency")
    @classmethod
    def usd(cls,v):
        if v.upper() != "USD": raise ValueError("Only USD is supported")
        return "USD"
