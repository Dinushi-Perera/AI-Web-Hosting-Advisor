from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import HostingPlan, CloudProvider, PricingSnapshot
from app.core.config import settings

def utcnow(): return datetime.now(timezone.utc)
class PricingService:
    def __init__(self,db:Session): self.db=db
    def list_plans(self,architecture:str|None=None,region:str|None=None):
        q=select(HostingPlan,CloudProvider).join(CloudProvider,CloudProvider.id==HostingPlan.provider_id)
        if architecture: q=q.where(HostingPlan.architecture_type==architecture)
        if region: q=q.where(HostingPlan.region==region)
        rows=self.db.execute(q.order_by(HostingPlan.base_monthly_cost)).all(); out=[]
        for p,provider in rows:
            snap=self.db.scalar(select(PricingSnapshot).where(PricingSnapshot.hosting_plan_id==p.id).order_by(PricingSnapshot.captured_at.desc()))
            lo=snap.min_monthly_cost if snap else p.base_monthly_cost; hi=snap.max_monthly_cost if snap else p.base_monthly_cost
            at=snap.captured_at if snap else p.updated_at
            age_days=(utcnow()-at.replace(tzinfo=at.tzinfo or timezone.utc)).days
            out.append({"id":p.id,"provider":provider.name,"plan":p.plan_name,"architecture":p.architecture_type,"region":p.region,"vcpu":p.vcpu,"ramGb":p.ram_gb,"storageGb":p.storage_gb,"monthlyRange":[round(lo,2),round(hi,2)],"currency":"USD","updatedAt":at.isoformat(),"source":snap.source if snap else p.source,"isDemo":p.is_demo,"isStale":age_days>settings.pricing_stale_days,"freshnessWarning":f"Pricing data is {age_days} days old." if age_days>settings.pricing_stale_days else None})
        return out
    def options(self,architecture:str,vcpu:int,ram:float,region:str|None=None):
        plans=self.list_plans(architecture,region)
        eligible=[p for p in plans if p["vcpu"]>=vcpu and p["ramGb"]>=ram]
        return eligible[:8] or [p for p in self.list_plans(architecture) if p["vcpu"]>=vcpu and p["ramGb"]>=ram][:8]
    def freshness(self,plans:list[dict])->float:
        if not plans:return 0.2
        vals=[]
        for p in plans:
            try:
                dt=datetime.fromisoformat(p["updatedAt"].replace("Z","+00:00")); age=(utcnow()-dt.replace(tzinfo=dt.tzinfo or timezone.utc)).days; vals.append(1.0 if age<=settings.pricing_stale_days else 0.5 if age<=90 else 0.2)
            except Exception: vals.append(0.2)
        return sum(vals)/len(vals)
