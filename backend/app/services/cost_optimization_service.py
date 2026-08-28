from typing import Any


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def budget_tier(budget: float | None) -> str:
    if budget is None:
        return "NOT_PROVIDED"
    return "STARTER" if budget < 50 else "GROWTH" if budget < 150 else "SCALE"


def optimize_cost(payload: dict, winner: str, resources: dict, selected_cost: dict, plans: list[dict]) -> dict:
    """Produce auditable optimization guidance from model sizing and stored prices only."""
    budget = _number(payload.get("budget") or payload.get("monthly_budget"))
    current = _number(payload.get("currentMonthlyCost") or payload.get("current_monthly_cost"))
    lo, hi = _number(selected_cost.get("min")), _number(selected_cost.get("max"))
    midpoint = round((lo + hi) / 2, 2) if lo is not None and hi is not None else None
    cheapest = min(plans, key=lambda row: row["monthlyRange"][0]) if plans else None
    savings = round(max(0, current - midpoint), 2) if current is not None and midpoint is not None else None
    actions = [
        {"priority": 1, "title": "Start with the model-sized resources", "detail": f"Use {resources.get('vcpu')} vCPU and {resources.get('ram_gb')} GB RAM as the initial right-sized baseline; validate utilization before scaling."},
        {"priority": 2, "title": "Use the lowest matching stored plan", "detail": f"{cheapest['provider']} {cheapest['plan']} has the lowest stored matching minimum at USD {cheapest['monthlyRange'][0]:.2f}/month." if cheapest else "No stored plan matches the required vCPU and RAM, so no provider saving is claimed."},
        {"priority": 3, "title": "Control variable services", "detail": "Set transfer, log-retention, backup, database, and autoscaling budgets with alerts before production traffic grows."},
    ]
    if winner == "KUBERNETES":
        actions.append({"priority": 4, "title": "Measure cluster overhead", "detail": "Track node requests versus usage and consolidate under-used workloads; Kubernetes control and operations overhead must be justified by scale."})
    elif winner == "CLOUD_VM":
        actions.append({"priority": 4, "title": "Use commitments after observation", "detail": "Run on flexible pricing first, then consider a commitment only after several weeks of stable baseline usage."})
    else:
        actions.append({"priority": 4, "title": "Avoid premature platform complexity", "detail": "Keep the VPS architecture simple until traffic, availability, or team requirements justify a managed cloud migration."})
    return {
        "method": "MODEL_RIGHT_SIZING_PLUS_STORED_PRICING",
        "budget_tier": budget_tier(budget),
        "budget": budget,
        "current_monthly_cost": current,
        "optimized_monthly_range": {"min": lo, "max": hi, "midpoint": midpoint},
        "estimated_monthly_savings": savings,
        "estimated_annual_savings": round(savings * 12, 2) if savings is not None else None,
        "savings_status": "CALCULATED_FROM_USER_CURRENT_COST" if savings is not None else "CURRENT_COST_NOT_PROVIDED",
        "right_sizing": resources,
        "lowest_matching_plan": cheapest,
        "actions": actions,
        "guardrail": "Savings are estimated only when the user supplies a current monthly cost; provider prices remain stored evidence, not an LLM estimate.",
    }
