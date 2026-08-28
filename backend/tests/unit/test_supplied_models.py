from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import MLModelVersion
from app.core.config import settings
from app.services.ml_service import MODEL_FEATURES, build_model_features, predict, predict_resources, resolve_model_path
from app.services import ml_service
from app.core.exceptions import AppError
import pytest


def _inputs():
    payload = {
        "websiteType": "SaaS", "monthlyUsers": "50000", "requestsPerUser": "12",
        "budget": "120", "growth": "Rapid Growth", "trafficPattern": "Business Hours",
        "apiCalls": "High", "backgroundJobs": "Yes", "realTime": "Notifications",
        "uptime": "99.95%", "autoscaling": "Yes",
        "managedDatabase": True, "experience": "Intermediate",
    }
    workload = {
        "concurrent_users": 250, "estimated_rps": 50, "peak_rps": 100,
        "database_intensity": "HIGH", "storage_gb": 100, "bandwidth_gb": 900,
    }
    return payload, workload


def test_supplied_classifier_and_resource_models_execute():
    assert resolve_model_path(settings.classifier_model_path).name == "LogisticRegression_full5000.joblib"
    assert resolve_model_path(settings.resource_model_path).name == "RandomForestRegressor_full5000.joblib"
    payload, workload = _inputs()
    features = build_model_features(payload, workload, [], [], "PLANNED")
    assert list(features) == MODEL_FEATURES

    engine = create_engine("sqlite://")
    MLModelVersion.__table__.create(engine)
    with Session(engine) as db:
        classifier = predict(db, features, workload, payload)

    resources = predict_resources(features, workload)
    assert classifier["is_trained_model"] is True
    assert classifier["model_version"] == "LogisticRegression_full5000"
    assert classifier["predicted_class"] in {"VPS", "CLOUD_VM", "KUBERNETES"}
    assert abs(sum(classifier["probabilities"].values()) - 1) < 0.001
    assert resources is not None
    assert resources["model_source"] == "TRAINED_MODEL"
    assert resources["model_version"] == "RandomForestRegressor_full5000"
    assert resources["vcpu"] in {1, 2, 4, 8, 16, 32, 64}
    assert resources["ram_gb"] in {2, 4, 8, 16, 32, 64, 128}


def test_hosting_recommendation_fails_closed_when_classifier_is_unavailable(monkeypatch):
    payload, workload = _inputs()
    features = build_model_features(payload, workload, [], [], "PLANNED")
    monkeypatch.setattr(ml_service, "_artifact", lambda path: (None, None))
    with Session(create_engine("sqlite://")) as db:
        with pytest.raises(AppError, match="trained Logistic Regression classifier is unavailable") as exc:
            predict(db, features, workload, payload)
    assert exc.value.code == "CLASSIFIER_MODEL_UNAVAILABLE"
