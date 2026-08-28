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

class ProjectPatch(BaseModel):
    model_config=ConfigDict(extra="allow")
    title: str | None = None
    name: str | None = None
    status: str | None = None
    input: dict[str, Any] | None = None

class LiveFrontendRequest(BaseModel):
    projectName: str = Field(min_length=2,max_length=120)
    websiteUrl: str
    category: str
    monthlyVisitors: int = Field(ge=0,le=1_000_000_000)
    concurrentUsers: int = Field(ge=1,le=1_000_000)
    growth: str
    trafficPattern: str
    budget: float = Field(ge=0,le=1_000_000)
    budgetFlexibility: str
    managesServers: bool
    highAvailability: bool
    rapidScaling: bool
    kubernetesSkill: bool
    managedDatabase: bool
    backups: bool

class PlannedFrontendRequest(BaseModel):
    model_config=ConfigDict(extra="allow")
    projectName: str = Field(min_length=2,max_length=120)
    websiteType: str = Field(min_length=1,max_length=80)
    description: str = Field(default="",max_length=1000)
    concurrentUsers: int | None = Field(default=None,ge=1,le=1_000_000)
    monthlyUsers: int | None = Field(default=None,ge=0,le=1_000_000_000)
    requestsPerUser: float | None = Field(default=None,ge=0.1,le=100_000)
    storage: float = Field(default=50,ge=0,le=10_000_000)
    budget: float = Field(ge=0,le=1_000_000)
    @field_validator("concurrentUsers","monthlyUsers","requestsPerUser",mode="before")
    @classmethod
    def optional_numbers(cls,v): return None if v in (None,"","Unknown","I don't know") else v

class IdeaFrontendRequest(BaseModel):
    model_config=ConfigDict(extra="allow")
    projectName: str | None = None
    idea: str = Field(min_length=20,max_length=5000)
    description: str | None = None
    industry: str = Field(min_length=1,max_length=100)
    targetUsers: str = Field(min_length=2,max_length=500)
    features: list[str] = Field(min_length=1,max_length=50)
    traffic: str = Field(min_length=1,max_length=100)
    budget: float = Field(ge=0,le=1_000_000)
    timeline: str = Field(min_length=1,max_length=100)
    experience: str = Field(min_length=1,max_length=100)
