from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import CloudProvider,HostingPlan,PricingSnapshot

def main():
    db=SessionLocal()
    try:
        providers={}
        for name in ["DigitalOcean","Hetzner","AWS","Google Cloud","Azure","Vultr"]:
            p=db.scalar(select(CloudProvider).where(CloudProvider.name==name))
            if not p:p=CloudProvider(name=name,slug=name.lower().replace(" ","-"));db.add(p);db.flush()
            providers[name]=p
        demo=[("DigitalOcean","Demo Basic 2x4","VPS","Singapore",2,4,80,2000,24,28),("Hetzner","Demo CPX 2x4","VPS","Singapore",2,4,80,1000,18,24),("DigitalOcean","Demo General 4x8","CLOUD_VM","Singapore",4,8,160,4000,55,75),("AWS","Demo General VM 4x8","CLOUD_VM","Singapore",4,8,100,0,70,110),("Google Cloud","Demo General VM 4x8","CLOUD_VM","Singapore",4,8,100,0,75,120),("Azure","Demo General VM 4x8","CLOUD_VM","Singapore",4,8,100,0,80,125),("DigitalOcean","Demo Managed K8s Baseline","KUBERNETES","Singapore",4,8,100,2000,120,180),("AWS","Demo Managed K8s Baseline","KUBERNETES","Singapore",4,8,100,0,150,240)]
        for provider,name,arch,region,vcpu,ram,storage,bw,lo,hi in demo:
            exists=db.scalar(select(HostingPlan).where(HostingPlan.provider_id==providers[provider].id,HostingPlan.plan_name==name))
            if exists:continue
            hp=HostingPlan(provider_id=providers[provider].id,plan_name=name,architecture_type=arch,region=region,vcpu=vcpu,ram_gb=ram,storage_gb=storage,bandwidth_gb=bw or None,managed=arch=="KUBERNETES",high_availability_supported=arch!="VPS",autoscaling_supported=arch=="KUBERNETES",base_monthly_cost=lo,currency="USD",source="DEMO_SEED_NOT_LIVE",is_demo=True);db.add(hp);db.flush();db.add(PricingSnapshot(hosting_plan_id=hp.id,min_monthly_cost=lo,max_monthly_cost=hi,currency="USD",components={"note":"Illustrative stored demo range only; replace with verified provider data."},source="DEMO_SEED_NOT_LIVE"))
        db.commit();print("Provider and pricing seed complete. Seed pricing is explicitly demo/non-live and USD-only.")
    finally:db.close()
if __name__=="__main__":main()
