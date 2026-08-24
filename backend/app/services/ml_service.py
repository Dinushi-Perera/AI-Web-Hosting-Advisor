from functools import lru_cache
import logging
from pathlib import Path
from typing import Any
import warnings

import joblib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import MLModelVersion

logger = logging.getLogger(__name__)

CLASSIFIER_VERSION = "hosting-classifier-selected-full5000"
RESOURCE_VERSION = "resource-sizer-selected-full5000"
MODEL_FEATURES = [
    "monthly_users", "expected_concurrent_users", "requests_per_user_min", "estimated_rps",
    "peak_rps", "budget_usd", "storage_gb", "performance_score", "performance_available",
    "cdn_present", "realtime_required", "realtime_connections", "background_jobs", "media_heavy",
    "high_availability", "multi_region_required", "autoscaling_required", "managed_database_preferred",
    "project_mode", "app_type", "database_intensity", "api_intensity", "growth_rate",
    "operational_skill", "availability_level", "traffic_pattern",
]


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "Unknown", "Not Decided", "Unsure", "I don't know"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _flag(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    return int(str(value or "").strip().lower() in {"1", "true", "yes", "required", "important", "critical"})


def _enum(value: Any, default: str) -> str:
    text = str(value or default).strip().upper().replace("/", "_").replace("-", "_").replace(" ", "_")
    return text.replace("%", "") or default


def _app_type(payload: dict) -> str:
    raw = _enum(payload.get("category") or payload.get("websiteType") or payload.get("app_type") or payload.get("industry"), "SAAS")
    aliases = {
        "E_COMMERCE": "ECOMMERCE", "FOOD": "MARKETPLACE", "FINANCE": "SAAS",
        "HEALTHCARE": "SAAS", "SOCIAL": "COMMUNITY", "ENTERTAINMENT": "MEDIA_STREAMING",
        "TRAVEL": "MARKETPLACE", "NON_PROFIT": "CORPORATE", "GOVERNMENT": "CORPORATE", "OTHER": "SAAS",
    }
    return aliases.get(raw, raw)


def _monthly_users(payload: dict, workload: dict) -> float:
    direct = _number(payload.get("monthlyVisitors") or payload.get("monthlyUsers") or payload.get("monthly_users"), -1)
    if direct >= 0:
        return direct
    daily = _number(payload.get("dailyUsers"), -1)
    if daily >= 0:
        return daily * 30
    audience = str(payload.get("audience") or payload.get("traffic") or "").lower()
    if "small" in audience:
        return 3_000
    if "growing" in audience:
        return 20_000
    if "national" in audience:
        return 125_000
    if "international" in audience:
        return 300_000
    if "large" in audience:
        return 1_500_000
    return max(1_000, _number(workload.get("concurrent_users"), 100) * 300)


def build_model_features(payload: dict, workload: dict, tech: list[dict], perf: list[dict], mode: str) -> dict:
    features_text = " ".join(str(item) for item in payload.get("features", [])).lower()
    realtime_value = payload.get("realTime") or payload.get("realtime_required")
    realtime = _flag(realtime_value) or int(any(item in features_text for item in ("chat", "real-time", "tracking")))
    media = str(payload.get("mediaUsage") or payload.get("media_usage") or "").lower()
    available_scores = [float(item["performance_score"]) for item in perf if item.get("status") == "AVAILABLE" and item.get("performance_score") is not None]
    cdn_declared = payload.get("cdn") not in (None, "", "None", "Not Decided", "Unknown")
    cdn_detected = any("cdn" in str(item.get("category", "")).lower() or str(item.get("technology", "")).lower() in {"cloudflare", "cloudfront", "fastly"} for item in tech)
    concurrent = _number(workload.get("concurrent_users"), 100)
    skill = payload.get("experience") or payload.get("operational_skill")
    if not skill:
        skill = "ADVANCED" if _flag(payload.get("kubernetesSkill")) else "INTERMEDIATE" if _flag(payload.get("managesServers")) else "BEGINNER"
    uptime = _enum(payload.get("uptime") or payload.get("availability_level"), "BASIC")
    if uptime not in {"BASIC", "99.5", "99.9", "99.95", "99.99"}:
        uptime = "BASIC"
    growth = _enum(payload.get("growth") or payload.get("growth_rate"), "MEDIUM").replace("_GROWTH", "")
    if growth not in {"STABLE", "SLOW", "MEDIUM", "RAPID"}:
        growth = "MEDIUM"
    traffic_pattern = _enum(payload.get("trafficPattern") or payload.get("traffic_pattern"), "NORMAL")
    if traffic_pattern not in {"NORMAL", "BUSINESS_HOURS", "EVENING", "WEEKEND", "EVENT_DRIVEN", "SEASONAL"}:
        traffic_pattern = "NORMAL"
    db_intensity = _enum(workload.get("database_intensity"), "MEDIUM")
    api_intensity = _enum(payload.get("apiCalls") or payload.get("api_intensity"), "MEDIUM")
    operational_skill = _enum(skill, "BEGINNER")
    return {
        "monthly_users": _monthly_users(payload, workload),
        "expected_concurrent_users": concurrent,
        "requests_per_user_min": _number(payload.get("requestsPerUser") or payload.get("requests_per_user_per_minute"), 10),
        "estimated_rps": _number(workload.get("estimated_rps")),
        "peak_rps": _number(workload.get("peak_rps")),
        "budget_usd": _number(payload.get("budget") or payload.get("monthly_budget")),
        "storage_gb": _number(workload.get("storage_gb"), 50),
        "performance_score": sum(available_scores) / len(available_scores) if available_scores else 0,
        "performance_available": int(bool(available_scores)),
        "cdn_present": int(cdn_declared or cdn_detected),
        "realtime_required": realtime,
        "realtime_connections": _number(payload.get("realtimeConnections"), concurrent if realtime else 0),
        "background_jobs": _flag(payload.get("backgroundJobs") or payload.get("background_jobs")),
        "media_heavy": int(media in {"high", "streaming"} or "video" in features_text),
        "high_availability": _flag(payload.get("highAvailability")) or int(uptime in {"99.95", "99.99"}),
        "multi_region_required": _flag(payload.get("multiRegion") or payload.get("multi_region_required")),
        "autoscaling_required": _flag(payload.get("autoscaling") or payload.get("rapidScaling") or payload.get("autoscaling_required")),
        "managed_database_preferred": _flag(payload.get("managedDatabase") or payload.get("managed_database_preferred")),
        "project_mode": mode,
        "app_type": _app_type(payload),
        "database_intensity": db_intensity if db_intensity in {"LOW", "MEDIUM", "HIGH", "VERY_HIGH"} else "MEDIUM",
        "api_intensity": api_intensity if api_intensity in {"LOW", "MEDIUM", "HIGH", "VERY_HIGH"} else "MEDIUM",
        "growth_rate": growth,
        "operational_skill": operational_skill if operational_skill in {"BEGINNER", "INTERMEDIATE", "ADVANCED"} else "BEGINNER",
        "availability_level": uptime,
        "traffic_pattern": traffic_pattern,
    }


def resolve_model_path(configured: str) -> Path | None:
    path = Path(configured)
    candidates = [path] if path.is_absolute() else [Path.cwd() / path, Path(__file__).resolve().parents[3] / path, Path(__file__).resolve().parents[2] / path]
    return next((candidate.resolve() for candidate in candidates if candidate.exists()), None)


@lru_cache(maxsize=8)
def _load_model(path: str, modified_ns: int):
    del modified_ns
    # Older joblib artifacts touch NumPy's deprecated shape setter while loading;
    # this is harmless and scoped only to trusted, bundled model deserialization.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Setting the shape on a NumPy array has been deprecated", category=DeprecationWarning)
        return joblib.load(path)


def _artifact(configured: str):
    path = resolve_model_path(configured)
    if not path:
        return None, None
    return _load_model(str(path), path.stat().st_mtime_ns), path


def _frame(model, features: dict) -> pd.DataFrame:
    names = list(getattr(model, "feature_names_in_", MODEL_FEATURES))
    return pd.DataFrame([{name: features.get(name, 0) for name in names}], columns=names)


def heuristic(workload: dict, payload: dict):
    peak = float(workload.get("peak_rps") or 0)
    budget = float(payload.get("budget") or payload.get("monthly_budget") or 0)
    kskill = bool(payload.get("kubernetesSkill")) or str(payload.get("operational_skill", "")).upper() == "ADVANCED"
    if peak < 30:
        probs = {"VPS": 0.72, "CLOUD_VM": 0.24, "KUBERNETES": 0.04}
    elif peak < 400:
        probs = {"VPS": 0.18, "CLOUD_VM": 0.74, "KUBERNETES": 0.08}
    else:
        probs = {"VPS": 0.05, "CLOUD_VM": 0.55, "KUBERNETES": 0.40}
    if budget and budget < 80:
        probs["KUBERNETES"] *= 0.5
        probs["VPS"] += 0.05
    if kskill and peak > 400:
        probs["KUBERNETES"] += 0.15
        probs["CLOUD_VM"] -= 0.08
    total = sum(max(0, value) for value in probs.values())
    probs = {key: round(max(0, value) / total, 4) for key, value in probs.items()}
    return {"predicted_class": max(probs, key=probs.get), "probabilities": probs, "model_version": "RULE_FALLBACK", "model_version_id": None, "is_trained_model": False}


def _classifier_prediction(model, features: dict, version: str, model_id: str | None = None) -> dict:
    probabilities = model.predict_proba(_frame(model, features))[0]
    classes = list(model.classes_)
    probs = {str(name): round(float(value), 6) for name, value in zip(classes, probabilities)}
    return {"predicted_class": str(classes[int(probabilities.argmax())]), "probabilities": probs, "model_version": version, "model_version_id": model_id, "is_trained_model": True}


def predict(db: Session, features: dict, workload: dict, payload: dict):
    version = db.scalar(select(MLModelVersion).where(MLModelVersion.is_active.is_(True)).order_by(MLModelVersion.created_at.desc()))
    candidates: list[tuple[str, str, str | None]] = []
    if version:
        candidates.append((version.model_path, version.version, version.id))
    candidates.append((settings.classifier_model_path, CLASSIFIER_VERSION, None))
    for configured, label, model_id in candidates:
        try:
            model, _ = _artifact(configured)
            if model is not None:
                return _classifier_prediction(model, features, label, model_id)
        except Exception:
            logger.exception("Classifier model could not be loaded or executed", extra={"model_path": configured})
    return heuristic(workload, payload)


def _nearest_tier(value: float, tiers: list[int]) -> int:
    return min(tiers, key=lambda tier: abs(tier - value))


def predict_resources(features: dict, workload: dict) -> dict | None:
    try:
        model, _ = _artifact(settings.resource_model_path)
        if model is None:
            return None
        raw = model.predict(_frame(model, features))[0]
        return {
            "vcpu": _nearest_tier(max(1.0, float(raw[0])), [1, 2, 4, 8, 16, 32, 64]),
            "ram_gb": _nearest_tier(max(2.0, float(raw[1])), [2, 4, 8, 16, 32, 64, 128]),
            "storage_gb": max(40, int(_number(workload.get("storage_gb"), 50))),
            "transfer_tb": max(1, round(_number(workload.get("bandwidth_gb"), 500) / 1000, 1)),
            "model_source": "TRAINED_MODEL",
            "model_version": RESOURCE_VERSION,
        }
    except Exception:
        logger.exception("Resource model could not be loaded or executed", extra={"model_path": settings.resource_model_path})
        return None


def bundled_model_status() -> dict:
    classifier = resolve_model_path(settings.classifier_model_path)
    resource = resolve_model_path(settings.resource_model_path)
    return {
        "classifier": {"available": classifier is not None, "version": CLASSIFIER_VERSION, "algorithm": "LogisticRegression", "accuracy": 0.973333, "f1": 0.973369, "evaluationSet": "independent_validation_cases_300.csv"},
        "resource": {"available": resource is not None, "version": RESOURCE_VERSION, "algorithm": "RandomForestRegressor", "vcpuMae": 0.6371, "ramMae": 0.9788, "vcpuR2": 0.9847, "ramR2": 0.9853, "evaluationSet": "independent_validation_cases_300.csv"},
    }
