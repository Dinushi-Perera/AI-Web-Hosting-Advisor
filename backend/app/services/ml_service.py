from pathlib import Path
import joblib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import MLModelVersion

def heuristic(workload:dict,payload:dict):
    peak=float(workload.get("peak_rps") or 0); budget=float(payload.get("budget") or payload.get("monthly_budget") or 0); kskill=bool(payload.get("kubernetesSkill")) or str(payload.get("operational_skill","")).upper()=="ADVANCED"
    if peak<30: probs={"VPS":0.72,"CLOUD_VM":0.24,"KUBERNETES":0.04}
    elif peak<400: probs={"VPS":0.18,"CLOUD_VM":0.74,"KUBERNETES":0.08}
    else: probs={"VPS":0.05,"CLOUD_VM":0.55,"KUBERNETES":0.40}
    if budget and budget<80: probs["KUBERNETES"]*=0.5; probs["VPS"]+=0.05
    if kskill and peak>400: probs["KUBERNETES"]+=0.15; probs["CLOUD_VM"]-=0.08
    total=sum(max(0,v) for v in probs.values()); probs={k:round(max(0,v)/total,4) for k,v in probs.items()}
    pred=max(probs,key=probs.get); return {"predicted_class":pred,"probabilities":probs,"model_version":"RULE_FALLBACK","is_trained_model":False}

def predict(db:Session,features:dict,workload:dict,payload:dict):
    version=db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)).order_by(MLModelVersion.created_at.desc()))
    if not version or not Path(version.model_path).exists(): return heuristic(workload,payload)
    try:
        pipe=joblib.load(version.model_path); proba=pipe.predict_proba(pd.DataFrame([features]))[0]; classes=list(pipe.classes_); probs={str(c):round(float(p),4) for c,p in zip(classes,proba)}; pred=str(classes[int(proba.argmax())]); return {"predicted_class":pred,"probabilities":probs,"model_version":version.version,"is_trained_model":True}
    except Exception: return heuristic(workload,payload)
