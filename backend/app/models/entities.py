from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

def uuid4str() -> str: return str(uuid4())
def utcnow() -> datetime: return datetime.now(timezone.utc)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class User(Base, TimestampMixin):
    __tablename__="users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="USER", index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_key: Mapped[str|None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str] = mapped_column(String(30), default="BEGINNER")
    default_region: Mapped[str] = mapped_column(String(80), default="Sri Lanka")
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Colombo")

class UserPreference(Base, TimestampMixin):
    __tablename__="user_preferences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    theme: Mapped[str] = mapped_column(String(20), default="SYSTEM")
    default_currency: Mapped[str] = mapped_column(String(3), default="USD")
    default_region: Mapped[str] = mapped_column(String(80), default="Sri Lanka")
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Colombo")
    chart_animations: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    analysis_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

class UserSession(Base):
    __tablename__="user_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    device: Mapped[str|None] = mapped_column(String(120), nullable=True)
    browser: Mapped[str|None] = mapped_column(String(120), nullable=True)
    ip_masked: Mapped[str|None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)

class PasswordResetToken(Base):
    __tablename__="password_reset_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    nonce_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Project(Base, TimestampMixin):
    __tablename__="projects"
    __table_args__=(Index("ix_projects_user_status","user_id","status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    mode: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    website_url: Mapped[str|None] = mapped_column(String(2048), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    target_region: Mapped[str|None] = mapped_column(String(80), nullable=True)
    latest_analysis_run_id: Mapped[str|None] = mapped_column(String(36), nullable=True)
    user_preferred_option: Mapped[str|None] = mapped_column(String(30), nullable=True)
    recommendation_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)

class ProjectInput(Base, TimestampMixin):
    __tablename__="project_inputs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)

class AnalysisRun(Base):
    __tablename__="analysis_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str|None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    started_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AnalysisJob(Base):
    __tablename__="analysis_jobs"
    __table_args__=(Index("ix_jobs_project_status","project_id","status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    current_stage: Mapped[str|None] = mapped_column(String(60), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stages_json: Mapped[list] = mapped_column(JSON, default=list)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str|None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str|None] = mapped_column(String(500), nullable=True)
    worker_id: Mapped[str|None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TechnologyDetection(Base, TimestampMixin):
    __tablename__="technology_detections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    technology: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float)
    confidence_label: Mapped[str] = mapped_column(String(30))
    user_correction: Mapped[dict|None] = mapped_column(JSON, nullable=True)

class TechnologyEvidence(Base):
    __tablename__="technology_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    detection_id: Mapped[str] = mapped_column(ForeignKey("technology_detections.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(60))
    pattern: Mapped[str] = mapped_column(String(255))
    value_masked: Mapped[str|None] = mapped_column(String(255), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

class PerformanceAudit(Base):
    __tablename__="performance_audits"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    strategy: Mapped[str] = mapped_column(String(20), default="MOBILE")
    status: Mapped[str] = mapped_column(String(30), default="AVAILABLE")
    performance_score: Mapped[float|None] = mapped_column(Float, nullable=True)
    accessibility_score: Mapped[float|None] = mapped_column(Float, nullable=True)
    best_practices_score: Mapped[float|None] = mapped_column(Float, nullable=True)
    seo_score: Mapped[float|None] = mapped_column(Float, nullable=True)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(80), default="PageSpeed Insights")
    warning: Mapped[str|None] = mapped_column(String(500), nullable=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class WorkloadEstimate(Base):
    __tablename__="workload_estimates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    concurrent_users: Mapped[int|None] = mapped_column(Integer, nullable=True)
    estimated_rps: Mapped[float|None] = mapped_column(Float, nullable=True)
    peak_rps: Mapped[float|None] = mapped_column(Float, nullable=True)
    classification: Mapped[str] = mapped_column(String(30))
    database_intensity: Mapped[str|None] = mapped_column(String(30), nullable=True)
    storage_gb: Mapped[float|None] = mapped_column(Float, nullable=True)
    bandwidth_gb: Mapped[float|None] = mapped_column(Float, nullable=True)
    growth_level: Mapped[str|None] = mapped_column(String(30), nullable=True)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    evidence_quality: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class LoadTestPlan(Base, TimestampMixin):
    __tablename__="load_test_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_type: Mapped[str] = mapped_column(String(20))
    virtual_users: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    target_url: Mapped[str] = mapped_column(String(2048))
    response_time_threshold_ms: Mapped[int] = mapped_column(Integer, default=2000)
    error_rate_threshold: Mapped[float] = mapped_column(Float, default=0.01)
    stages: Mapped[list] = mapped_column(JSON, default=list)
    script: Mapped[Text] = mapped_column(Text)
    file_key: Mapped[str|None] = mapped_column(String(255), nullable=True)
    safety_notes: Mapped[list] = mapped_column(JSON, default=list)

class CloudProvider(Base, TimestampMixin):
    __tablename__="cloud_providers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class HostingPlan(Base, TimestampMixin):
    __tablename__="hosting_plans"
    __table_args__=(Index("ix_hosting_provider_region","provider_id","region"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    provider_id: Mapped[str] = mapped_column(ForeignKey("cloud_providers.id", ondelete="CASCADE"), index=True)
    plan_name: Mapped[str] = mapped_column(String(160))
    architecture_type: Mapped[str] = mapped_column(String(30), index=True)
    region: Mapped[str] = mapped_column(String(80), index=True)
    vcpu: Mapped[int] = mapped_column(Integer)
    ram_gb: Mapped[float] = mapped_column(Float)
    storage_gb: Mapped[float] = mapped_column(Float)
    bandwidth_gb: Mapped[float|None] = mapped_column(Float, nullable=True)
    managed: Mapped[bool] = mapped_column(Boolean, default=False)
    high_availability_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    autoscaling_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    base_monthly_cost: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    source: Mapped[str] = mapped_column(String(255), default="APPLICATION_MANAGED")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

class PricingSnapshot(Base):
    __tablename__="pricing_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    hosting_plan_id: Mapped[str] = mapped_column(ForeignKey("hosting_plans.id", ondelete="CASCADE"), index=True)
    min_monthly_cost: Mapped[float] = mapped_column(Float)
    max_monthly_cost: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(255))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class Recommendation(Base):
    __tablename__="recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), unique=True, index=True)
    recommended_option: Mapped[str] = mapped_column(String(30))
    overall_score: Mapped[float] = mapped_column(Float)
    confidence_value: Mapped[float] = mapped_column(Float)
    confidence_label: Mapped[str] = mapped_column(String(30))
    resource_size: Mapped[dict] = mapped_column(JSON, default=dict)
    estimated_cost: Mapped[dict] = mapped_column(JSON, default=dict)
    alternatives: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    rule_results: Mapped[list] = mapped_column(JSON, default=list)
    model_version: Mapped[str|None] = mapped_column(String(60), nullable=True)
    model_probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class RecommendationScore(Base):
    __tablename__="recommendation_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    option: Mapped[str] = mapped_column(String(30))
    score: Mapped[float] = mapped_column(Float)
    ml_probability: Mapped[float] = mapped_column(Float, default=0.0)
    budget_fit: Mapped[float] = mapped_column(Float, default=0.0)
    traffic_fit: Mapped[float] = mapped_column(Float, default=0.0)
    scalability_fit: Mapped[float] = mapped_column(Float, default=0.0)
    reliability_fit: Mapped[float] = mapped_column(Float, default=0.0)
    operational_fit: Mapped[float] = mapped_column(Float, default=0.0)
    rule_adjustments: Mapped[list] = mapped_column(JSON, default=list)

class Optimization(Base, TimestampMixin):
    __tablename__="optimization_suggestions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(180))
    explanation: Mapped[Text] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(String(160))
    difficulty: Mapped[str] = mapped_column(String(20))
    benefit: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True)
    steps: Mapped[list] = mapped_column(JSON, default=list)

class Report(Base):
    __tablename__="reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="READY")
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    file_key: Mapped[str|None] = mapped_column(String(255), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)

class Notification(Base):
    __tablename__="notifications"
    __table_args__=(Index("ix_notifications_user_read","user_id","is_read"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Feedback(Base):
    __tablename__="user_feedback"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    clarity_rating: Mapped[int] = mapped_column(Integer)
    usefulness_rating: Mapped[int] = mapped_column(Integer)
    ease_of_use_rating: Mapped[int] = mapped_column(Integer)
    recommendation_trust_rating: Mapped[int] = mapped_column(Integer)
    comments: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    actor_user_id: Mapped[str|None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str|None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[str|None] = mapped_column(String(80), nullable=True)
    ip_masked: Mapped[str|None] = mapped_column(String(80), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class MLModelVersion(Base):
    __tablename__="ml_model_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    version: Mapped[str] = mapped_column(String(60), unique=True)
    algorithm: Mapped[str] = mapped_column(String(120))
    training_rows: Mapped[int] = mapped_column(Integer)
    feature_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    accuracy: Mapped[float|None] = mapped_column(Float, nullable=True)
    precision: Mapped[float|None] = mapped_column(Float, nullable=True)
    recall: Mapped[float|None] = mapped_column(Float, nullable=True)
    f1: Mapped[float|None] = mapped_column(Float, nullable=True)
    confusion_matrix: Mapped[list] = mapped_column(JSON, default=list)
    class_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_importance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    model_path: Mapped[str] = mapped_column(String(255))

class ModelPrediction(Base):
    __tablename__="model_predictions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    model_version_id: Mapped[str|None] = mapped_column(ForeignKey("ml_model_versions.id", ondelete="SET NULL"), nullable=True)
    predicted_class: Mapped[str] = mapped_column(String(30))
    probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TestResult(Base):
    __tablename__="test_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    test_type: Mapped[str] = mapped_column(String(10), index=True)
    test_name: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(30), index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    duration_ms: Mapped[int|None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

class ModelTrainingJob(Base):
    __tablename__="model_training_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    current_stage: Mapped[str] = mapped_column(String(30), default="QUEUED")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    dataset_path: Mapped[str] = mapped_column(String(255))
    result_model_id: Mapped[str|None] = mapped_column(String(36), nullable=True)
    error_message: Mapped[str|None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
