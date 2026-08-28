from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.security import validate_password

class RegisterRequest(BaseModel):
    fullName: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str
    @field_validator("password")
    @classmethod
    def strong(cls,v): validate_password(v); return v
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class ForgotPasswordRequest(BaseModel): email: EmailStr
class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    @field_validator("password")
    @classmethod
    def strong(cls,v): validate_password(v); return v
class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str
    @field_validator("newPassword")
    @classmethod
    def strong(cls,v): validate_password(v); return v
