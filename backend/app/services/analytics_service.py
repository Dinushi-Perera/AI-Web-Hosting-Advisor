from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Optimization, PerformanceAudit, Project, Recommendation, Report
from app.services.project_service import ProjectService


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _cost_point(recommendation: Recommendation, project_names: dict[str, str]) -> dict | None:
    cost = recommendation.estimated_cost or {}
    optimization = recommendation.cost_optimization or {}
    optimized = optimization.get("optimized_monthly_range") or {}
    minimum = _number(cost.get("min"))
    maximum = _number(cost.get("max"))
    midpoint = _number(optimized.get("midpoint"))
    if midpoint is None and minimum is not None and maximum is not None:
        midpoint = round((minimum + maximum) / 2, 2)
    if midpoint is None:
        return None
    return {
        "id": recommendation.id,
        "recorded_at": recommendation.created_at.isoformat(),
        "project_id": recommendation.project_id,
        "project_name": project_names.get(recommendation.project_id, "Project"),
        "current": _number(optimization.get("current_monthly_cost")),
        "recommended": midpoint,
        "recommended_min": minimum,
        "recommended_max": maximum,
        "currency": "USD",
    }


def dashboard(db: Session, user):
    projects = list(db.scalars(select(Project).where(Project.user_id == user.id, Project.deleted_at.is_(None))))
    project_ids = [project.id for project in projects]
    completed = sum(1 for project in projects if project.status == "COMPLETED")
    performance = []
    recommendations = []
    reports = []
    high_priority = 0
    if project_ids:
        performance = list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.project_id.in_(project_ids), PerformanceAudit.strategy == "MOBILE", PerformanceAudit.performance_score.is_not(None))))
        recommendations = list(db.scalars(select(Recommendation).where(Recommendation.project_id.in_(project_ids))))
        reports = list(db.scalars(select(Report).where(Report.project_id.in_(project_ids), Report.deleted_at.is_(None))))
        high_priority = db.scalar(select(func.count(Optimization.id)).where(Optimization.project_id.in_(project_ids), Optimization.priority.in_(["HIGH", "CRITICAL"]), Optimization.status == "OPEN")) or 0

    average_performance = round(sum(item.performance_score for item in performance) / len(performance)) if performance else None
    distribution = {"VPS": 0, "CLOUD_VM": 0, "KUBERNETES": 0}
    for recommendation in recommendations:
        distribution[recommendation.recommended_option] = distribution.get(recommendation.recommended_option, 0) + 1

    project_names = {project.id: project.title for project in projects}
    ordered_recommendations = sorted(recommendations, key=lambda item: item.created_at)
    cost_trend = [point for item in ordered_recommendations if (point := _cost_point(item, project_names)) is not None][-30:]
    latest_by_project = {item.project_id: item for item in ordered_recommendations}
    savings = [_number((item.cost_optimization or {}).get("estimated_monthly_savings")) for item in latest_by_project.values()]
    evidenced_savings = [value for value in savings if value is not None]

    recent = sorted(projects, key=lambda project: project.updated_at, reverse=True)[:5]
    activity = list(db.scalars(select(AuditLog).where(AuditLog.actor_user_id == user.id).order_by(AuditLog.created_at.desc()).limit(15)))
    return {
        "summary": {
            "total_projects": len(projects),
            "completed_analyses": completed,
            "average_performance_score": average_performance,
            "estimated_monthly_savings": round(sum(evidenced_savings), 2) if evidenced_savings else None,
            "reports_generated": len(reports),
            "high_priority_issues": high_priority,
            "currency": "USD",
        },
        "recent_projects": [ProjectService(db).serialize(project) for project in recent],
        "performance_trend": [{"date": item.audited_at.isoformat(), "performance": item.performance_score, "project_id": item.project_id} for item in sorted(performance, key=lambda row: row.audited_at)[-30:]],
        "hosting_distribution": distribution,
        "cost_trend": cost_trend,
        "cost_summary": {
            "currency": "USD",
            "points": len(cost_trend),
            "note": "Each point is a persisted analysis cost update. Current cost is included only when supplied; recommended cost is the midpoint of the stored USD range.",
        },
        "priority_issues": high_priority,
        "recent_activity": [{"id": item.id, "action": item.action, "projectId": item.entity_id if item.entity_type == "PROJECT" else None, "projectTitle": project_names.get(item.entity_id), "timestamp": item.created_at.isoformat(), "metadata": item.metadata_json} for item in activity],
    }
