from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import Notification
router=APIRouter(prefix="/notifications",tags=["Notifications"])
def nj(n): return {"id":n.id,"type":n.type,"title":n.title,"message":n.message,"isRead":n.is_read,"data":n.data,"createdAt":n.created_at.isoformat()}
@router.get("")
def list_notifications(user=Depends(get_current_user),db:Session=Depends(get_db)): return [nj(n) for n in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(100))]
@router.patch("/{notification_id}/read")
def read(notification_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    n=db.get(Notification,notification_id)
    if not n or n.user_id!=user.id: raise AppError("NOTIFICATION_NOT_FOUND","Notification not found.",404)
    n.is_read=True; db.commit(); return nj(n)
@router.post("/read-all")
def read_all(user=Depends(get_current_user),db:Session=Depends(get_db)):
    for n in db.scalars(select(Notification).where(Notification.user_id==user.id,Notification.is_read.is_(False))): n.is_read=True
    db.commit(); return {"success":True}
@router.delete("/{notification_id}")
def delete(notification_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    n=db.get(Notification,notification_id)
    if not n or n.user_id!=user.id: raise AppError("NOTIFICATION_NOT_FOUND","Notification not found.",404)
    db.delete(n); db.commit(); return {"success":True}
