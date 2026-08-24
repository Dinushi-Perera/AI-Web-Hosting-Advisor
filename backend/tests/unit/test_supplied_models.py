from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import MLModelVersion
from app.services.ml_service import MODEL_FEATURES, build_model_features, predict, predict_resources


def _inputs():
    payload = {
        "websiteType": "SaaS", "monthlyUsers": "50000", "requestsPerUser": "12",
        "budget": "120", "growth": "Rapid Growth", "trafficPattern": "Business Hours",
        "apiCalls": "High", "backgroundJobs": "Yes", "realTime": "Notifications",
        "uptime": "99.95%", "multiRegion": "No", "autoscaling": "Yes",
        "managedDatabase": True, "experience": "Intermediate",
    }
    workload = {
        "concurrent_users": 250, "estimated_rps": 50, "peak_rps": 100,
        "database_intensity": "HIGH", "storage_gb": 100, "bandwidth_gb": 900,
    }
    return payload, workload


def test_supplied_classifier_and_resource_models_execute():
    payload, workload = _inputs()
    features = build_model_features(payload, workload, [], [], "PLANNED")
    assert list(features) == MODEL_FEATURES

    engine = create_engine("sqlite://")
    MLModelVersion.__table__.create(engine)
    with Session(engine) as db:
        classifier = predict(db, features, workload, payload)

    resources = predict_resources(features, workload)
    assert classifier["is_trained_model"] is True
    assert classifier["predicted_class"] in {"VPS", "CLOUD_VM", "KUBERNETES"}
    assert abs(sum(classifier["probabilities"].values()) - 1) < 0.001
    assert resources is not None
    assert resources["model_source"] == "TRAINED_MODEL"
    assert resources["vcpu"] in {1, 2, 4, 8, 16, 32, 64}
    assert resources["ram_gb"] in {2, 4, 8, 16, 32, 64, 128}
