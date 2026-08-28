from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.analytics_service import _cost_point


def test_cost_point_uses_persisted_range_midpoint_and_current_cost():
    recommendation = SimpleNamespace(
        id="recommendation-1",
        project_id="project-1",
        created_at=datetime(2026, 8, 27, 10, 30, tzinfo=timezone.utc),
        estimated_cost={"min": 40, "max": 60},
        cost_optimization={"current_monthly_cost": 75},
    )

    point = _cost_point(recommendation, {"project-1": "Store"})

    assert point == {
        "id": "recommendation-1",
        "recorded_at": "2026-08-27T10:30:00+00:00",
        "project_id": "project-1",
        "project_name": "Store",
        "current": 75.0,
        "recommended": 50.0,
        "recommended_min": 40.0,
        "recommended_max": 60.0,
        "currency": "USD",
    }


def test_cost_point_keeps_recommendation_when_current_cost_was_not_supplied():
    recommendation = SimpleNamespace(
        id="recommendation-2",
        project_id="project-1",
        created_at=datetime(2026, 8, 27, 11, 0, tzinfo=timezone.utc),
        estimated_cost={"min": 80, "max": 120},
        cost_optimization={},
    )

    point = _cost_point(recommendation, {"project-1": "Store"})

    assert point["current"] is None
    assert point["recommended"] == 100.0
