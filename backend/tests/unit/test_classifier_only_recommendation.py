import pytest

from app.services import recommendation_service as recommendations


class _Pricing:
    def __init__(self, db):
        self.db = db

    def options(self, *args, **kwargs):
        return []

    def freshness(self, plans):
        return 0.5


@pytest.mark.parametrize("predicted_class", ["VPS", "CLOUD_VM", "KUBERNETES"])
def test_recommendation_is_exactly_the_classifier_prediction(monkeypatch, predicted_class):
    probabilities = {option: 0.05 for option in ("VPS", "CLOUD_VM", "KUBERNETES")}
    probabilities[predicted_class] = 0.9
    monkeypatch.setattr(recommendations, "predict", lambda *args: {
        "predicted_class": predicted_class,
        "probabilities": probabilities,
        "model_version": "LogisticRegression_full5000",
        "model_version_id": None,
        "is_trained_model": True,
    })
    monkeypatch.setattr(recommendations, "predict_resources", lambda *args: {"vcpu": 2, "ram_gb": 4, "storage_gb": 50, "transfer_tb": 1, "model_source": "TRAINED_MODEL", "model_version": "RandomForestRegressor_full5000"})
    monkeypatch.setattr(recommendations, "PricingService", _Pricing)
    monkeypatch.setattr(recommendations, "explain_with_llm", lambda context: {"status": "DISABLED", "warning": None})

    result = recommendations.build(None, {"budget": 100}, {"peak_rps": 10, "evidence_quality": 0.5}, [], [], 1.0)

    assert result["recommended_option"] == predicted_class
    assert result["decision_evidence"]["method"] == "TRAINED_LOGISTIC_REGRESSION_ARGMAX"
    assert result["rule_results"] == []
    assert result["ranking_method"]["weights"] == {"trained_logistic_regression_probability": 1.0}
