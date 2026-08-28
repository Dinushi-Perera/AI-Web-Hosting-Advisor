import json

from app.services.cost_optimization_service import optimize_cost
from app.services import openrouter_explanation_service as llm


def _context():
    return {
        "decision": {
            "recommended_option": "CLOUD_VM",
            "estimated_cost": {"min": 40, "max": 70},
            "reasons": [{"note": "Traffic fit"}],
            "alternatives": [{"display_name": "Cloud VM", "score": 91, "weaknesses": []}],
            "assumptions": ["Traffic is estimated"],
        },
        "cost_optimization": {"actions": [{"title": "Right-size"}]},
    }


def test_cost_optimizer_uses_current_cost_and_stored_plan():
    plans = [{"provider": "Provider A", "plan": "Balanced", "monthlyRange": [40, 70]}]
    result = optimize_cost({"budget": 100, "currentMonthlyCost": 90}, "CLOUD_VM", {"vcpu": 4, "ram_gb": 8}, {"min": 40, "max": 70}, plans)
    assert result["budget_tier"] == "GROWTH"
    assert result["estimated_monthly_savings"] == 35
    assert result["estimated_annual_savings"] == 420
    assert result["lowest_matching_plan"]["provider"] == "Provider A"


def test_cost_optimizer_never_invents_savings_without_current_cost():
    result = optimize_cost({"budget": 45}, "VPS", {"vcpu": 2, "ram_gb": 4}, {"min": 12, "max": 24}, [])
    assert result["estimated_monthly_savings"] is None
    assert result["savings_status"] == "CURRENT_COST_NOT_PROVIDED"


def test_llm_disabled_returns_complete_deterministic_explanation(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_enabled", False)
    result = llm.explain(_context())
    assert result["status"] == "DISABLED"
    assert result["source"] == "DETERMINISTIC_TEMPLATE"
    assert result["content"]["cost_explanation"]


def test_openrouter_glm_structured_response_is_used_without_recalculating(monkeypatch):
    generated = {"summary": "Cloud VM is the best persisted fit.", "why_best": ["Traffic"], "cost_explanation": "USD 40–70 from stored data.", "model_explanation": "Two models contributed.", "tradeoffs": [], "optimization_priorities": ["Right-size"], "assumptions": []}

    class FakeResponse:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"model": "z-ai/glm-5.2:free", "choices": [{"message": {"role": "assistant", "content": json.dumps(generated)}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50}}

    monkeypatch.setattr(llm.settings, "llm_enabled", True)
    monkeypatch.setattr(llm.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(llm.httpx, "post", lambda *args, **kwargs: FakeResponse())
    result = llm.explain(_context())
    assert result["status"] == "GENERATED"
    assert result["source"] == "OPENROUTER_CHAT_COMPLETIONS"
    assert result["model"] == "z-ai/glm-5.2:free"
    assert result["content"] == generated
