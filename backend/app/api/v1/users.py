from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.user import UserPatch,PreferencePatch
from app.models import User,UserPreference,UserSession,AuditLog
from app.services.auth_service import mask_ip,utcnow
from app.core.exceptions import AppError
router=APIRouter(prefix="/users",tags=["Users"])
def uj(u): return {"id":u.id,"fullName":u.full_name,"email":u.email,"role":u.role.lower(),"experienceLevel":u.experience_level.title(),"defaultRegion":u.default_region,"currency":"USD","timezone":u.timezone,"avatar":u.avatar_key,"avatarUrl":"/users/me/avatar" if u.avatar_key else None}
@router.get("/me")
def get_me(user=Depends(get_current_user)): return uj(user)
@router.patch("/me")
def patch_me(req:UserPatch,user=Depends(get_current_user),db:Session=Depends(get_db)):
    d=req.model_dump(exclude_none=True)
    if "email" in d:
        email=str(d["email"]).lower()
        existing=db.scalar(select(User).where(User.email==email,User.id!=user.id))
        if existing: raise AppError("AUTH_EMAIL_EXISTS","An account already exists for this email.",409)
    if "fullName" in d:user.full_name=d["fullName"].strip()
    if "email" in d:user.email=str(d["email"]).lower()
    if "experienceLevel" in d:user.experience_level=d["experienceLevel"].upper()
    if "defaultRegion" in d:user.default_region=d["defaultRegion"]
    if "timezone" in d:user.timezone=d["timezone"]
    db.add(AuditLog(actor_user_id=user.id,action="PROFILE_UPDATE",entity_type="USER",entity_id=user.id,metadata_json={"fields":sorted(d.keys())}))
    db.commit(); return uj(user)
@router.post("/me/avatar")
async def avatar(file:UploadFile=File(...),user=Depends(get_current_user),db:Session=Depends(get_db)):
    allowed={"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}
    if file.content_type not in allowed: raise AppError("VALIDATION_ERROR","Avatar must be PNG, JPG or WebP.",422)
    data=await file.read(2_000_001)
    if len(data)>2_000_000: raise AppError("VALIDATION_ERROR","Avatar must be 2 MB or smaller.",422)
    folder=Path("storage/avatars"); folder.mkdir(parents=True,exist_ok=True)
    old=folder/Path(user.avatar_key).name if user.avatar_key else None
    key=f"{user.id}-{uuid4().hex}.{allowed[file.content_type]}"; (folder/key).write_bytes(data)
    if old and old.exists(): old.unlink()
    user.avatar_key=key; db.add(AuditLog(actor_user_id=user.id,action="AVATAR_UPDATE",entity_type="USER",entity_id=user.id)); db.commit(); return {"avatar":key,"avatarUrl":"/users/me/avatar"}
@router.get("/me/avatar")
def get_avatar(user=Depends(get_current_user)):
    if not user.avatar_key: raise AppError("AVATAR_NOT_FOUND","Profile image not found.",404)
    path=Path("storage/avatars")/Path(user.avatar_key).name
    if not path.exists(): raise AppError("AVATAR_NOT_FOUND","Profile image not found.",404)
    return FileResponse(path)
@router.delete("/me/avatar")
def remove_avatar(user=Depends(get_current_user),db:Session=Depends(get_db)):
    if user.avatar_key:
        p=Path("storage/avatars")/Path(user.avatar_key).name
        if p.exists(): p.unlink()
    user.avatar_key=None; db.add(AuditLog(actor_user_id=user.id,action="AVATAR_REMOVE",entity_type="USER",entity_id=user.id)); db.commit(); return {"success":True}
@router.get("/me/preferences")
def preferences(user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(UserPreference).where(UserPreference.user_id==user.id))
    return {"theme":p.theme.lower(),"defaultCurrency":"USD","defaultRegion":p.default_region,"timezone":p.timezone,"chartAnimations":p.chart_animations,"emailNotifications":p.email_notifications,"analysisNotifications":p.analysis_notifications,"onboardingCompleted":p.onboarding_completed}
@router.patch("/me/preferences")
def patch_preferences(req:PreferencePatch,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=db.scalar(select(UserPreference).where(UserPreference.user_id==user.id)); d=req.model_dump(exclude_none=True)
    mp={"theme":"theme","defaultRegion":"default_region","timezone":"timezone","chartAnimations":"chart_animations","emailNotifications":"email_notifications","analysisNotifications":"analysis_notifications","onboardingCompleted":"onboarding_completed"}
    for k,a in mp.items():
        if k in d:setattr(p,a,d[k].upper() if k=="theme" else d[k])
    p.default_currency="USD"; db.add(AuditLog(actor_user_id=user.id,action="PREFERENCES_UPDATE",entity_type="USER_PREFERENCE",entity_id=p.id,metadata_json={"fields":sorted(d.keys())})); db.commit(); return preferences(user,db)
@router.get("/me/sessions")
def sessions(user=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=list(db.scalars(select(UserSession).where(UserSession.user_id==user.id,UserSession.revoked_at.is_(None)).order_by(UserSession.last_active_at.desc())))
    return [{"id":s.id,"device":s.device,"browser":s.browser,"ip":s.ip_masked,"lastActive":s.last_active_at.isoformat(),"current":False} for s in rows]
@router.delete("/me/sessions/{session_id}")
def revoke(session_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    s=db.get(UserSession,session_id)
    if not s or s.user_id!=user.id: raise AppError("SESSION_NOT_FOUND","Session not found.",404)
    s.revoked_at=utcnow(); db.commit(); return {"success":True}
@router.delete("/me/sessions")
def revoke_all(user=Depends(get_current_user),db:Session=Depends(get_db)):
    for s in db.scalars(select(UserSession).where(UserSession.user_id==user.id,UserSession.revoked_at.is_(None))): s.revoked_at=utcnow()
    db.commit(); return {"success":True}
