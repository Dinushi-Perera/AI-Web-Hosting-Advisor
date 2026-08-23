from fastapi import Depends, Header, Cookie, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import AppError
from app.models import User

def get_current_user(request:Request,db:Session=Depends(get_db),authorization:str|None=Header(default=None),advisor_session:str|None=Cookie(default=None)):
    token=None
    if authorization and authorization.lower().startswith("bearer "): token=authorization.split(" ",1)[1].strip()
    token=token or advisor_session
    if not token: raise AppError("AUTH_REQUIRED","Authentication is required.",401)
    try: p=decode_token(token,"access")
    except ValueError: raise AppError("AUTH_REQUIRED","Authentication is required.",401)
    u=db.get(User,p.get("sub"))
    if not u or u.status!="ACTIVE": raise AppError("AUTH_REQUIRED","Authentication is required.",401)
    request.state.user_id=u.id
    return u
