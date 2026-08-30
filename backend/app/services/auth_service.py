import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import UserSession, PasswordResetToken, AuditLog
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, create_password_reset_token, token_hash, decode_token
from app.core.exceptions import AppError
from app.core.config import settings
from app.services.mail_service import send_password_reset_email

def utcnow(): return datetime.now(timezone.utc)
def mask_ip(ip: str | None):
    if not ip: return None
    if ":" in ip: return ip.split(":")[0]+"::***"
    p=ip.split("."); return ".".join(p[:2]+["***","***"]) if len(p)==4 else "***"

class AuthService:
    def __init__(self,db:Session): self.db=db; self.users=UserRepository(db)
    def register(self,full_name,email,password):
        normalized_email=email.strip().lower()
        if self.users.by_email(normalized_email):
            raise AppError("AUTH_EMAIL_EXISTS","An account already exists for this email.",409)
        try:
            u=self.users.create(full_name=full_name.strip(),email=normalized_email,password_hash=hash_password(password),status="ACTIVE")
            self.db.add(AuditLog(actor_user_id=u.id,action="REGISTER",entity_type="USER",entity_id=u.id))
            self.db.commit()
        except IntegrityError as exc:
            # The database unique constraint is the final guard when two
            # registration requests for the same email arrive concurrently.
            self.db.rollback()
            if self.users.by_email(normalized_email):
                raise AppError("AUTH_EMAIL_EXISTS","An account already exists for this email.",409) from exc
            raise
        return u
    def login(self,email,password,ip=None,user_agent=None):
        u=self.users.by_email(email)
        now=utcnow()
        if not u or u.status!="ACTIVE": raise AppError("AUTH_INVALID_CREDENTIALS","Invalid email or password.",401)
        if u.locked_until and u.locked_until.replace(tzinfo=u.locked_until.tzinfo or timezone.utc)>now: raise AppError("AUTH_TEMP_LOCKED","Too many failed attempts. Try again later.",429)
        if not verify_password(password,u.password_hash):
            u.failed_login_count=(u.failed_login_count or 0)+1
            if u.failed_login_count>=5: u.locked_until=now+timedelta(minutes=10); u.failed_login_count=0
            self.db.commit(); raise AppError("AUTH_INVALID_CREDENTIALS","Invalid email or password.",401)
        u.failed_login_count=0; u.locked_until=None; u.last_login_at=now
        s=UserSession(user_id=u.id,refresh_token_hash="pending",device=(user_agent or "Unknown")[:120],browser=(user_agent or "Unknown")[:120],ip_masked=mask_ip(ip),expires_at=now+timedelta(days=settings.refresh_token_days))
        self.db.add(s); self.db.flush()
        refresh=create_refresh_token(u.id,s.id); s.refresh_token_hash=token_hash(refresh)
        access=create_access_token(u.id,u.role)
        self.db.add(AuditLog(actor_user_id=u.id,action="LOGIN",entity_type="USER_SESSION",entity_id=s.id,ip_masked=mask_ip(ip)))
        self.db.commit(); return u,access,refresh,s
    def refresh(self,refresh_token:str):
        payload=decode_token(refresh_token,"refresh"); sid=payload.get("sid"); uid=payload.get("sub")
        s=self.db.get(UserSession,sid)
        if not s or s.user_id!=uid or s.revoked_at or s.refresh_token_hash!=token_hash(refresh_token): raise AppError("AUTH_INVALID_SESSION","Session is invalid or expired.",401)
        u=self.users.by_id(uid)
        if not u or u.status!="ACTIVE": raise AppError("AUTH_INVALID_SESSION","Session is invalid or expired.",401)
        s.last_active_at=utcnow(); self.db.commit(); return create_access_token(u.id,u.role)
    def logout(self,refresh_token:str|None):
        if refresh_token:
            try:
                p=decode_token(refresh_token,"refresh"); s=self.db.get(UserSession,p.get("sid"))
                if s and not s.revoked_at: s.revoked_at=utcnow(); self.db.commit()
            except Exception: pass
    def forgot_password(self,email:str):
        if (not settings.smtp_host or not settings.smtp_from_email) and not settings.password_reset_return_token:
            raise AppError("EMAIL_NOT_CONFIGURED","Password reset email is not configured. Configure the SMTP settings and try again.",503)
        u=self.users.by_email(email)
        token=None
        if u:
            now=utcnow()
            for old in self.db.scalars(select(PasswordResetToken).where(PasswordResetToken.user_id==u.id,PasswordResetToken.used_at.is_(None))):
                old.used_at=now
            nonce=hashlib.sha256(f"{u.id}:{utcnow().timestamp()}".encode()).hexdigest()[:32]
            row=PasswordResetToken(user_id=u.id,nonce_hash=hashlib.sha256(nonce.encode()).hexdigest(),expires_at=now+timedelta(minutes=settings.password_reset_minutes))
            self.db.add(row); self.db.flush(); token=create_password_reset_token(u.id,nonce)
            send_password_reset_email(u.email,u.full_name,token)
            self.db.add(AuditLog(actor_user_id=u.id,action="PASSWORD_RESET_REQUEST",entity_type="USER",entity_id=u.id))
            self.db.commit()
        return token
    def reset_password(self,token,password):
        try: p=decode_token(token,"password_reset")
        except ValueError as exc: raise AppError("AUTH_RESET_INVALID","Reset token is invalid or expired.",400) from exc
        uid=p.get("sub"); nonce=p.get("nonce")
        if not uid or not nonce: raise AppError("AUTH_RESET_INVALID","Reset token is invalid or expired.",400)
        nh=hashlib.sha256(nonce.encode()).hexdigest(); row=self.db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id==uid,PasswordResetToken.nonce_hash==nh,PasswordResetToken.used_at.is_(None)).order_by(PasswordResetToken.created_at.desc()))
        if not row or row.expires_at.replace(tzinfo=row.expires_at.tzinfo or timezone.utc)<utcnow(): raise AppError("AUTH_RESET_INVALID","Reset token is invalid or expired.",400)
        u=self.users.by_id(uid)
        if not u: raise AppError("AUTH_RESET_INVALID","Reset token is invalid or expired.",400)
        u.password_hash=hash_password(password); row.used_at=utcnow()
        for s in self.db.scalars(select(UserSession).where(UserSession.user_id==uid,UserSession.revoked_at.is_(None))): s.revoked_at=utcnow()
        self.db.add(AuditLog(actor_user_id=uid,action="PASSWORD_RESET",entity_type="USER",entity_id=uid)); self.db.commit()
    def change_password(self,user,current,new):
        if not verify_password(current,user.password_hash): raise AppError("AUTH_INVALID_CREDENTIALS","Current password is incorrect.",400)
        user.password_hash=hash_password(new); self.db.add(AuditLog(actor_user_id=user.id,action="PASSWORD_CHANGE",entity_type="USER",entity_id=user.id)); self.db.commit()
