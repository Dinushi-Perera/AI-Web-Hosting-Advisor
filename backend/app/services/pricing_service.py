from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import HostingPlan, CloudProvider, PricingSnapshot
from app.core.config import settings

def utcnow(): return datetime.now(timezone.utc)
class PricingService:
    def __init__(self,db:Session): self.db=db
    def providers(self):
        return list(self.db.scalars(select(CloudProvider).order_by(CloudProvider.name)))
    def list_plans(self,architecture:str|None=None):
        q=select(HostingPlan,CloudProvider).join(CloudProvider,CloudProvider.id==HostingPlan.provider_id)
        if architecture: q=q.where(HostingPlan.architecture_type==architecture)
        rows=self.db.execute(q.order_by(HostingPlan.base_monthly_cost)).all(); out=[]
        for p,provider in rows:
            snap=self.db.scalar(select(PricingSnapshot).where(PricingSnapshot.hosting_plan_id==p.id).order_by(PricingSnapshot.captured_at.desc()))
            lo=snap.min_monthly_cost if snap else p.base_monthly_cost; hi=snap.max_monthly_cost if snap else p.base_monthly_cost
            at=snap.captured_at if snap else p.updated_at
            age_days=(utcnow()-at.replace(tzinfo=at.tzinfo or timezone.utc)).days
            out.append({"id":p.id,"provider":provider.name,"plan":p.plan_name,"architecture":p.architecture_type,"vcpu":p.vcpu,"ramGb":p.ram_gb,"storageGb":p.storage_gb,"monthlyRange":[round(lo,2),round(hi,2)],"currency":"USD","updatedAt":at.isoformat(),"source":snap.source if snap else p.source,"isDemo":p.is_demo,"isStale":age_days>settings.pricing_stale_days,"freshnessWarning":f"Pricing data is {age_days} days old." if age_days>settings.pricing_stale_days else None})
        return out
    def options(self,architecture:str,vcpu:int,ram:float):
        plans=self.list_plans(architecture)
        eligible=[p for p in plans if p["vcpu"]>=vcpu and p["ramGb"]>=ram]
        if eligible:return eligible[:8]
        all_architecture=self.list_plans(architecture)
        eligible=[p for p in all_architecture if p["vcpu"]>=vcpu and p["ramGb"]>=ram]
        if eligible:return eligible[:8]
        # When the pricing cache has no sufficiently large SKU, extrapolate from
        # the largest same-architecture records. This remains traceable to stored
        # evidence and is explicitly labelled; it is not presented as a real SKU.
        bases=plans or all_architecture
        estimates=[]
        for base in sorted(bases,key=lambda p:(p["vcpu"],p["ramGb"]),reverse=True)[:3]:
            factor=max(1.0,vcpu/max(base["vcpu"],1),ram/max(base["ramGb"],1))
            row={**base,"id":f"estimate-{base['id']}-{vcpu}-{ram}","plan":f"{base['plan']} · model-scaled estimate","basePlan":base["plan"],"baseVcpu":base["vcpu"],"baseRamGb":base["ramGb"],"vcpu":vcpu,"ramGb":ram,"monthlyRange":[round(base["monthlyRange"][0]*factor,2),round(base["monthlyRange"][1]*factor,2)],"source":f"{base.get('source','Stored pricing')} · resource-ratio extrapolation","isEstimate":True,"pricingMethod":"RESOURCE_RATIO_EXTRAPOLATION","scaleFactor":round(factor,3)}
            estimates.append(row)
        return estimates
    def freshness(self,plans:list[dict])->float:
        if not plans:return 0.2
        vals=[]
        for p in plans:
            try:
                dt=datetime.fromisoformat(p["updatedAt"].replace("Z","+00:00")); age=(utcnow()-dt.replace(tzinfo=dt.tzinfo or timezone.utc)).days; vals.append(1.0 if age<=settings.pricing_stale_days else 0.5 if age<=90 else 0.2)
            except Exception: vals.append(0.2)
        return sum(vals)/len(vals)
