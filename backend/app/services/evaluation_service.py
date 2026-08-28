from functools import lru_cache
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.services.ml_service import resolve_model_path

ROOT=Path(__file__).resolve().parents[3]

def _dataset(name:str)->Path:return ROOT/"dataset"/name

@lru_cache(maxsize=1)
def evaluate_supplied_assets()->dict:
    # scikit-learn imports SciPy's native extensions. Loading it only when the
    # evaluation endpoint is used prevents a transient Windows Application
    # Control check from stopping the entire FastAPI application at startup.
    from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,mean_absolute_error,r2_score

    files={name:_dataset(name) for name in ("hosting_advisor_master_5000.csv","hosting_classifier_5000.csv","resource_sizing_5000.csv","independent_validation_cases_300.csv")}
    frames={name:pd.read_csv(path) for name,path in files.items()}
    validation=frames["independent_validation_cases_300.csv"]
    classifier_path=resolve_model_path(settings.classifier_model_path);resource_path=resolve_model_path(settings.resource_model_path)
    if not classifier_path or not resource_path:raise FileNotFoundError("The supplied production model artifacts are unavailable.")
    # The bundled artifacts were produced by an older NumPy version. The
    # deprecated shape setter is used by joblib while reading trusted arrays,
    # but it does not affect the loaded models or their predictions.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Setting the shape on a NumPy array has been deprecated", category=DeprecationWarning)
        classifier=joblib.load(classifier_path);resource=joblib.load(resource_path)
    classifier_features=list(classifier.feature_names_in_);resource_features=list(resource.feature_names_in_)
    predicted=classifier.predict(validation[classifier_features]);actual=validation["hosting_type"]
    labels=[str(x) for x in classifier.classes_];report=classification_report(actual,predicted,labels=labels,output_dict=True,zero_division=0)
    resource_pred=resource.predict(validation[resource_features]);vcpu_actual=validation["recommended_vcpu"].to_numpy();ram_actual=validation["recommended_ram_gb"].to_numpy()
    classifier_estimator=classifier.steps[-1][1] if hasattr(classifier,"steps") else classifier
    resource_estimator=resource.steps[-1][1] if hasattr(resource,"steps") else resource
    importance=getattr(classifier_estimator,"feature_importances_",None)
    if importance is None and hasattr(classifier_estimator,"coef_"):importance=np.mean(np.abs(classifier_estimator.coef_),axis=0)
    ranked=sorted(zip(classifier_features,(importance if importance is not None else np.zeros(len(classifier_features)))),key=lambda x:float(x[1]),reverse=True)[:10]
    return {"datasets":[{"name":name,"rows":len(frame),"columns":len(frame.columns),"purpose":"Independent evaluation" if name.startswith("independent") else "Training and analysis"} for name,frame in frames.items()],"totalTrainingRows":5000,"validationRows":len(validation),"classifier":{"version":"LogisticRegression_full5000","artifact":classifier_path.name,"algorithm":type(classifier_estimator).__name__,"accuracy":float(accuracy_score(actual,predicted)),"precision":float(report["weighted avg"]["precision"]),"recall":float(report["weighted avg"]["recall"]),"f1":float(report["weighted avg"]["f1-score"]),"labels":labels,"confusionMatrix":confusion_matrix(actual,predicted,labels=labels).tolist(),"classMetrics":[{"label":label,"precision":float(report[label]["precision"]),"recall":float(report[label]["recall"]),"f1":float(report[label]["f1-score"]),"support":int(report[label]["support"])} for label in labels],"featureImportance":[{"feature":name,"importance":float(value)} for name,value in ranked]},"resource":{"version":"RandomForestRegressor_full5000","artifact":resource_path.name,"algorithm":type(resource_estimator).__name__,"vcpuMae":float(mean_absolute_error(vcpu_actual,resource_pred[:,0])),"ramMae":float(mean_absolute_error(ram_actual,resource_pred[:,1])),"vcpuR2":float(r2_score(vcpu_actual,resource_pred[:,0])),"ramR2":float(r2_score(ram_actual,resource_pred[:,1]))},"explanation":"Accuracy shows how often the hosting class was correct. Precision measures how reliable each recommendation was. Recall measures how many correct cases were found. MAE is the average resource-size error; lower is better. R-squared shows how much sizing variation the model explains; closer to 1 is better."}
