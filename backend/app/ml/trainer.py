from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from app.ml.features import NUMERIC_FEATURES,CATEGORICAL_FEATURES,ALL_FEATURES,TARGET

def validate_dataset(path:str):
    df=pd.read_csv(path); errors=[]
    missing=[c for c in ALL_FEATURES+[TARGET] if c not in df.columns]
    if missing: errors.append({"code":"MISSING_COLUMNS","columns":missing})
    if len(df)<30: errors.append({"code":"TOO_FEW_ROWS","message":"At least 30 rows are required for meaningful training."})
    if TARGET in df.columns:
        invalid=sorted(set(df[TARGET].dropna().astype(str))-{"VPS","CLOUD_VM","KUBERNETES"})
        if invalid: errors.append({"code":"INVALID_LABELS","values":invalid})
    return {"valid":not errors,"row_count":len(df),"duplicate_rows":int(df.duplicated().sum()),"errors":errors,"columns":list(df.columns)}

def train(path:str,output_dir:str="app/ml/models"):
    check=validate_dataset(path)
    if not check["valid"]: raise ValueError(str(check["errors"]))
    df=pd.read_csv(path).drop_duplicates(); X=df[ALL_FEATURES]; y=df[TARGET].astype(str)
    stratify=y if y.value_counts().min()>=2 else None
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42,stratify=stratify)
    num=Pipeline([("impute",SimpleImputer(strategy="median"))]); cat=Pipeline([("impute",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))])
    pre=ColumnTransformer([("num",num,NUMERIC_FEATURES),("cat",cat,CATEGORICAL_FEATURES)])
    pipe=Pipeline([("pre",pre),("model",RandomForestClassifier(n_estimators=250,random_state=42,class_weight="balanced"))]); pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
    acc=float(accuracy_score(yte,pred)); pr,rc,f1,_=precision_recall_fscore_support(yte,pred,average="weighted",zero_division=0)
    version=datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S"); Path(output_dir).mkdir(parents=True,exist_ok=True); model_path=str(Path(output_dir)/f"hosting_model_{version}.joblib"); joblib.dump(pipe,model_path)
    labels=["VPS","CLOUD_VM","KUBERNETES"]; cm=confusion_matrix(yte,pred,labels=labels).tolist()
    return {"version":version,"algorithm":"RandomForestClassifier","training_rows":len(Xtr),"feature_schema":{"numeric":NUMERIC_FEATURES,"categorical":CATEGORICAL_FEATURES,"target":TARGET},"accuracy":acc,"precision":float(pr),"recall":float(rc),"f1":float(f1),"confusion_matrix":cm,"class_distribution":y.value_counts().to_dict(),"feature_importance":{},"model_path":model_path}
