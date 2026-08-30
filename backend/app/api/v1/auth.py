from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response, Cookie
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegisterRequest,LoginRequest,ForgotPasswordRequest,ResetPasswordRequest,ChangePasswordRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.core.config import settings

router=APIRouter(prefix="/auth",tags=["Authentication"])
def user_json(u): return {"id":u.id,"fullName":u.full_name,"email":u.email,"role":u.role.lower(),"experienceLevel":u.experience_level.title(),"currency":"USD","timezone":u.timezone}
def set_cookies(response:Response,access:str,refresh:str):
    response.set_cookie("advisor_session",access,httponly=True,secure=settings.cookie_secure,samesite=settings.cookie_samesite,path="/",max_age=settings.access_token_minutes*60)
    response.set_cookie("advisor_refresh",refresh,httponly=True,secure=settings.cookie_secure,samesite=settings.cookie_samesite,path="/",max_age=settings.refresh_token_days*86400)
@router.post("/register",status_code=201)
def register(req:RegisterRequest,response:Response,request:Request,db:Session=Depends(get_db)):
    svc=AuthService(db); u=svc.register(req.fullName,req.email,req.password); u,access,refresh,_=svc.login(req.email,req.password,request.client.host if request.client else None,request.headers.get("user-agent")); set_cookies(response,access,refresh); return {"success":True,"message":"Registration successful.","user":user_json(u),"accessToken":access,"tokenType":"bearer"}
@router.post("/login")
def login(req:LoginRequest,response:Response,request:Request,db:Session=Depends(get_db)):
    u,access,refresh,_=AuthService(db).login(req.email,req.password,request.client.host if request.client else None,request.headers.get("user-agent")); set_cookies(response,access,refresh); return {"user":user_json(u),"accessToken":access,"tokenType":"bearer"}
@router.post("/logout")
def logout(response:Response,advisor_refresh:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    AuthService(db).logout(advisor_refresh); response.delete_cookie("advisor_session",path="/"); response.delete_cookie("advisor_refresh",path="/"); return {"success":True,"message":"Signed out."}
@router.post("/refresh")
def refresh(response:Response,advisor_refresh:str|None=Cookie(default=None),db:Session=Depends(get_db)):
    if not advisor_refresh: from app.core.exceptions import AppError; raise AppError("AUTH_INVALID_SESSION","Refresh session is missing.",401)
    access=AuthService(db).refresh(advisor_refresh); response.set_cookie("advisor_session",access,httponly=True,secure=settings.cookie_secure,samesite=settings.cookie_samesite,path="/",max_age=settings.access_token_minutes*60); return {"accessToken":access,"tokenType":"bearer"}
@router.get("/me")
def me(user=Depends(get_current_user)): return user_json(user)
@router.post("/forgot-password")
def forgot(req:ForgotPasswordRequest,db:Session=Depends(get_db)):
    token=AuthService(db).forgot_password(req.email); data={"message":"If an account exists for that email, a password reset link has been sent."}
    if settings.password_reset_return_token and token: data["developmentResetToken"]=token
    return data
@router.post("/reset-password")
def reset(req:ResetPasswordRequest,db:Session=Depends(get_db)): AuthService(db).reset_password(req.token,req.password); return {"success":True,"message":"Password updated. Please sign in again."}
@router.post("/change-password")
def change(req:ChangePasswordRequest,user=Depends(get_current_user),db:Session=Depends(get_db)): AuthService(db).change_password(user,req.currentPassword,req.newPassword); return {"success":True,"message":"Password updated."}
