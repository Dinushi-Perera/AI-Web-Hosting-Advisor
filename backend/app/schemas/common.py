from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict
T=TypeVar("T")
class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
    meta: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

def ok(data=None, message="OK", meta=None):
    return {"success": True, "message": message, "data": data, "meta": meta, "error": None}
