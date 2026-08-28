"""Recalculate persisted recommendations with the configured production models.

The default mode avoids outbound LLM calls. Pass ``--with-openrouter`` to also
regenerate every persisted explanation through the configured OpenRouter model.
"""
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import (
    ModelPrediction, PerformanceAudit, Project, ProjectInput, Recommendation,
    RecommendationScore, TechnologyDetection, WorkloadEstimate,
)
from app.services.recommendation_service import build


def workload_json(row: WorkloadEstimate) -> dict:
    return {
        "concurrent_users": row.concurrent_users,
        "estimated_rps": row.estimated_rps,
        "peak_rps": row.peak_rps,
        "classification": row.classification,
        "database_intensity": row.database_intensity,
        "storage_gb": row.storage_gb,
        "bandwidth_gb": row.bandwidth_gb,
        "growth_level": row.growth_level,
        "assumptions": row.assumptions or [],
        "evidence_quality": row.evidence_quality,
    }


def run(with_openrouter: bool = False) -> dict:
    original_llm = settings.llm_enabled
    settings.llm_enabled = bool(with_openrouter)
    updated = skipped = 0
    try:
        with SessionLocal() as db:
            recommendations = list(db.scalars(select(Recommendation).order_by(Recommendation.created_at)))
            for recommendation in recommendations:
                project = db.get(Project, recommendation.project_id)
                project_input = db.scalar(select(ProjectInput).where(ProjectInput.project_id == recommendation.project_id))
                workload = db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id == recommendation.analysis_run_id))
                if not project or not project_input or not workload:
                    skipped += 1
                    continue
                tech = [{"technology": row.technology, "confidence": row.confidence} for row in db.scalars(select(TechnologyDetection).where(TechnologyDetection.analysis_run_id == recommendation.analysis_run_id))]
                perf = [{"status": row.status, "performance_score": row.performance_score, "metrics": row.metrics_json or {}} for row in db.scalars(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id == recommendation.analysis_run_id))]
                result = build(db, project_input.payload or {}, workload_json(workload), tech, perf, project_input.completeness_score, project.mode)
                llm = result["llm_explanation"]
                if not with_openrouter:
                    llm["status"] = "DETERMINISTIC_BACKFILL"
                    llm["warning"] = "Model and cost evidence were recalculated; run the backfill with OpenRouter enabled to regenerate the live advisor explanation."
                for key in ("recommended_option", "overall_score", "resource_size", "estimated_cost", "cost_optimization", "decision_evidence", "alternatives", "reasons", "assumptions", "warnings", "rule_results", "model_version", "model_probabilities"):
                    setattr(recommendation, key, result[key])
                recommendation.confidence_value = result["confidence"]["value"]
                recommendation.confidence_label = result["confidence"]["label"]
                recommendation.llm_explanation = llm
                recommendation.llm_status = llm["status"]
                recommendation.llm_model = llm.get("model")
                db.execute(delete(RecommendationScore).where(RecommendationScore.recommendation_id == recommendation.id))
                score_fields = ("option", "score", "ml_probability", "budget_fit", "traffic_fit", "scalability_fit", "reliability_fit", "operational_fit", "rule_adjustments")
                for score in result["scores"]:
                    db.add(RecommendationScore(recommendation_id=recommendation.id, **{key: score[key] for key in score_fields}))
                prediction = db.scalar(select(ModelPrediction).where(ModelPrediction.analysis_run_id == recommendation.analysis_run_id))
                if prediction:
                    prediction.predicted_class = result["decision_evidence"]["classifier"]["output"]
                    prediction.probabilities = result["model_probabilities"]
                    prediction.features = result["model_features"]
                    prediction.model_version_id = result["model_version_id"]
                else:
                    db.add(ModelPrediction(analysis_run_id=recommendation.analysis_run_id, predicted_class=result["decision_evidence"]["classifier"]["output"], probabilities=result["model_probabilities"], features=result["model_features"], model_version_id=result["model_version_id"]))
                updated += 1
            db.commit()
            return {"updated": updated, "skipped": skipped, "classifier": settings.classifier_model_path, "resource": settings.resource_model_path}
    finally:
        settings.llm_enabled = original_llm


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--with-openrouter",action="store_true",help="Regenerate explanations with the configured OpenRouter model")
    args=parser.parse_args()
    print(run(with_openrouter=args.with_openrouter))
