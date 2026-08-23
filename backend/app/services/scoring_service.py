OPTIONS=["VPS","CLOUD_VM","KUBERNETES"]
def _clamp(v): return max(0,min(100,float(v)))
def resource_size(workload:dict,payload:dict):
    peak=float(workload.get("peak_rps") or 0); db=str(workload.get("database_intensity") or "MEDIUM")
    if peak<30: vcpu,ram=2,4
    elif peak<150: vcpu,ram=4,8
    elif peak<500: vcpu,ram=8,16
    else: vcpu,ram=16,32
    if db in {"HIGH","VERY_HIGH"}: ram*=1.5
    storage=max(40,int(float(workload.get("storage_gb") or 50)))
    return {"vcpu":vcpu,"ram_gb":int(ram),"storage_gb":storage,"transfer_tb":max(1,round(float(workload.get("bandwidth_gb") or 500)/1000,1))}
def score_options(workload:dict,payload:dict,ml:dict,rules:list):
    peak=float(workload.get("peak_rps") or 0); budget=float(payload.get("budget") or payload.get("monthly_budget") or 0)
    base={"VPS":55,"CLOUD_VM":65,"KUBERNETES":48}
    traffic={"VPS":95 if peak<30 else 75 if peak<100 else 45 if peak<300 else 20,"CLOUD_VM":70 if peak<30 else 92 if peak<500 else 80,"KUBERNETES":25 if peak<100 else 55 if peak<400 else 92}
    scale={"VPS":45,"CLOUD_VM":82,"KUBERNETES":98}; reliability={"VPS":55,"CLOUD_VM":86,"KUBERNETES":95}; operational={"VPS":95,"CLOUD_VM":82,"KUBERNETES":45 if not payload.get("kubernetesSkill") else 78}
    assumed_cost={"VPS":30,"CLOUD_VM":70,"KUBERNETES":180}; budget_fit={o:(80 if not budget else _clamp(100-(max(0,assumed_cost[o]-budget)/max(budget,1))*100)) for o in OPTIONS}
    result=[]
    for o in OPTIONS:
        mlfit=float(ml.get("probabilities",{}).get(o,0))*100
        s=0.35*mlfit+0.20*traffic[o]+0.15*budget_fit[o]+0.10*scale[o]+0.10*reliability[o]+0.10*operational[o]
        adjustments=[r for r in rules if r["option"]==o]; s+=sum(r["score_delta"] for r in adjustments)
        result.append({"option":o,"score":round(_clamp(s),1),"ml_probability":round(mlfit/100,4),"budget_fit":round(budget_fit[o],1),"traffic_fit":traffic[o],"scalability_fit":scale[o],"reliability_fit":reliability[o],"operational_fit":operational[o],"rule_adjustments":adjustments})
    return sorted(result,key=lambda x:x["score"],reverse=True)
