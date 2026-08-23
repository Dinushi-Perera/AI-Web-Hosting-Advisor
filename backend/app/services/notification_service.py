from sqlalchemy.orm import Session
from app.models import Notification
def create_notification(db:Session,user_id:str,type_:str,title:str,message:str,data:dict|None=None):
    n=Notification(user_id=user_id,type=type_,title=title,message=message,data=data or {}); db.add(n); return n
