import hashlib, re, secrets
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,128}$")

def validate_password(password: str) -> None:
    if not PASSWORD_RE.match(password):
        raise ValueError("Password must be 8-128 characters and include uppercase, lowercase, number and special character.")

def hash_password(password: str) -> str:
    validate_password(password)
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try: return pwd_context.verify(password, password_hash)
    except Exception: return False

def _token(subject: str, token_type: str, expires: timedelta, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "typ": token_type, "iat": now, "exp": now + expires, "jti": secrets.token_urlsafe(16)}
    if extra: payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_access_token(user_id: str, role: str) -> str:
    return _token(user_id, "access", timedelta(minutes=settings.access_token_minutes), {"role": role})

def create_refresh_token(user_id: str, session_id: str) -> str:
    return _token(user_id, "refresh", timedelta(days=settings.refresh_token_days), {"sid": session_id})

def create_password_reset_token(user_id: str, nonce: str) -> str:
    return _token(user_id, "password_reset", timedelta(minutes=settings.password_reset_minutes), {"nonce": nonce})

def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    if expected_type and payload.get("typ") != expected_type:
        raise ValueError("Invalid token type")
    return payload

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
