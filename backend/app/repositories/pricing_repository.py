from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import CloudProvider, HostingPlan, PricingSnapshot
class PricingRepository:
    def __init__(self,db:Session): self.db=db
    def providers(self): return list(self.db.scalars(select(CloudProvider).where(CloudProvider.active.is_(True)).order_by(CloudProvider.name)))
    def plans(self): return list(self.db.scalars(select(HostingPlan).order_by(HostingPlan.base_monthly_cost)))
    def latest_snapshot(self,plan_id:str): return self.db.scalar(select(PricingSnapshot).where(PricingSnapshot.hosting_plan_id==plan_id).order_by(PricingSnapshot.captured_at.desc()))
