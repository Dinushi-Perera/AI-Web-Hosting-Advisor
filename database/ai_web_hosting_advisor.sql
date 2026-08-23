SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE DATABASE IF NOT EXISTS ai_web_hosting_advisor
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE ai_web_hosting_advisor;

-- ============================================================================
-- 01. AUTHENTICATION & USERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    is_verified TINYINT NOT NULL DEFAULT 0,
    is_email_verified TINYINT GENERATED ALWAYS AS (is_verified) STORED,
    email_verified_at DATETIME(6) NULL,
    last_login_at DATETIME(6) NULL,
    failed_login_count INT NOT NULL DEFAULT 0,
    failed_login_attempts INT GENERATED ALWAYS AS (failed_login_count) STORED,
    locked_until DATETIME(6) NULL,
    avatar_key VARCHAR(255) NULL,
    experience_level VARCHAR(30) NOT NULL DEFAULT 'BEGINNER',
    default_region VARCHAR(80) NOT NULL DEFAULT 'Sri Lanka',
    timezone VARCHAR(80) NOT NULL DEFAULT 'Asia/Colombo',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_public_id (public_id),
    UNIQUE KEY uq_users_email (email),
    KEY ix_users_role (role),
    KEY ix_users_status (status),
    KEY ix_users_created_at (created_at),
    CONSTRAINT ck_users_role CHECK (role = 'USER'),
    CONSTRAINT ck_users_status CHECK (status IN ('ACTIVE','DISABLED','PENDING','LOCKED')),
    CONSTRAINT ck_users_failed_login_count CHECK (failed_login_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_preferences (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    theme VARCHAR(20) NOT NULL DEFAULT 'SYSTEM',
    -- Retained because the supplied backend ORM reads/writes this column.
    -- Database constraint guarantees USD-only behavior.
    default_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    default_region VARCHAR(80) NOT NULL DEFAULT 'Sri Lanka',
    timezone VARCHAR(80) NOT NULL DEFAULT 'Asia/Colombo',
    chart_animations TINYINT NOT NULL DEFAULT 1,
    email_notifications TINYINT NOT NULL DEFAULT 1,
    analysis_notifications TINYINT NOT NULL DEFAULT 1,
    onboarding_completed TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_preferences_user (user_id),
    CONSTRAINT fk_user_preferences_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT ck_user_preferences_theme CHECK (theme IN ('LIGHT','DARK','SYSTEM')),
    CONSTRAINT ck_user_preferences_currency CHECK (default_currency = 'USD')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    user_id VARCHAR(36) NOT NULL,
    refresh_token_hash VARCHAR(64) NOT NULL,
    device VARCHAR(120) NULL,
    browser VARCHAR(120) NULL,
    operating_system VARCHAR(120) NULL,
    ip_masked VARCHAR(80) NULL,
    user_agent_hash VARCHAR(128) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    last_active_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    expires_at DATETIME(6) NOT NULL,
    revoked_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_sessions_public_id (public_id),
    UNIQUE KEY uq_user_sessions_refresh_hash (refresh_token_hash),
    KEY ix_user_sessions_user (user_id),
    KEY ix_user_sessions_expires (expires_at),
    KEY ix_user_sessions_revoked (revoked_at),
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    nonce_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    used_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_password_reset_nonce_hash (nonce_hash),
    KEY ix_password_reset_user (user_id),
    KEY ix_password_reset_expires (expires_at),
    CONSTRAINT fk_password_reset_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 02. PROJECTS & INPUTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(160) NOT NULL,
    slug VARCHAR(190) NULL,
    mode VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    website_url VARCHAR(2048) NULL,
    website_category VARCHAR(80) NULL,
    -- Retained for backend API compatibility; strictly USD-only.
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    target_region VARCHAR(80) NULL,
    description TEXT NULL,
    latest_analysis_run_id VARCHAR(36) NULL,
    user_preferred_option VARCHAR(30) NULL,
    recommendation_stale TINYINT NOT NULL DEFAULT 0,
    is_demo TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    archived_at DATETIME(6) NULL,
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_projects_public_id (public_id),
    KEY ix_projects_user (user_id),
    KEY ix_projects_mode (mode),
    KEY ix_projects_status (status),
    KEY ix_projects_created (created_at),
    KEY ix_projects_updated (updated_at),
    KEY ix_projects_user_status (user_id, status),
    KEY ix_projects_user_created (user_id, created_at),
    KEY ix_projects_latest_run (latest_analysis_run_id),
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT ck_projects_mode CHECK (mode IN ('LIVE_URL','PLANNED','NEW_IDEA')),
    CONSTRAINT ck_projects_status CHECK (status IN ('DRAFT','QUEUED','ANALYSING','COMPLETED','NEEDS_ATTENTION','FAILED','CANCELLED','ARCHIVED')),
    CONSTRAINT ck_projects_currency CHECK (currency = 'USD'),
    CONSTRAINT ck_projects_preferred_option CHECK (user_preferred_option IS NULL OR user_preferred_option IN ('VPS','CLOUD_VM','KUBERNETES'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS project_inputs (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    -- Canonical compatibility payload used by the supplied FastAPI backend.
    payload JSON NOT NULL,
    completeness_score DECIMAL(6,5) NOT NULL DEFAULT 0.00000,

    -- Normalized advanced fields requested by the database specification.
    website_url VARCHAR(2048) NULL,
    normalized_url VARCHAR(2048) NULL,
    target_users_description TEXT NULL,
    target_region VARCHAR(80) NULL,
    expected_launch_date DATE NULL,
    frontend_framework VARCHAR(120) NULL,
    backend_framework VARCHAR(120) NULL,
    database_type VARCHAR(120) NULL,
    cms_type VARCHAR(120) NULL,
    cache_type VARCHAR(120) NULL,
    cdn_type VARCHAR(120) NULL,
    expected_daily_users BIGINT UNSIGNED NULL,
    expected_monthly_users BIGINT UNSIGNED NULL,
    peak_concurrent_users INT UNSIGNED NULL,
    requests_per_user_per_minute DECIMAL(10,4) NULL,
    traffic_growth VARCHAR(30) NULL,
    traffic_pattern VARCHAR(50) NULL,
    peak_multiplier DECIMAL(8,4) NULL,
    database_intensity VARCHAR(30) NULL,
    file_uploads_enabled TINYINT NULL,
    average_upload_size_mb DECIMAL(12,2) NULL,
    estimated_storage_gb DECIMAL(14,2) NULL,
    media_usage_level VARCHAR(30) NULL,
    api_intensity VARCHAR(30) NULL,
    background_jobs_enabled TINYINT NULL,
    real_time_features_enabled TINYINT NULL,
    expected_realtime_connections INT UNSIGNED NULL,
    required_uptime DECIMAL(6,3) NULL,
    automatic_backups_required TINYINT NULL,
    disaster_recovery_required TINYINT NULL,
    multi_region_required TINYINT NULL,
    autoscaling_required TINYINT NULL,
    monitoring_required TINYINT NULL,
    monthly_budget_usd DECIMAL(12,2) NULL,
    current_monthly_hosting_cost_usd DECIMAL(12,2) NULL,
    budget_flexibility VARCHAR(30) NULL,
    operational_skill VARCHAR(30) NULL,
    kubernetes_experience TINYINT NULL,
    managed_database_preferred TINYINT NULL,
    idea_description LONGTEXT NULL,
    industry VARCHAR(120) NULL,
    timeline_description VARCHAR(255) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_inputs_project (project_id),
    KEY ix_project_inputs_target_region (target_region),
    KEY ix_project_inputs_launch_date (expected_launch_date),
    CONSTRAINT fk_project_inputs_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT ck_project_inputs_completeness CHECK (completeness_score BETWEEN 0 AND 1),
    CONSTRAINT ck_project_inputs_budget CHECK (monthly_budget_usd IS NULL OR monthly_budget_usd >= 0),
    CONSTRAINT ck_project_inputs_current_cost CHECK (current_monthly_hosting_cost_usd IS NULL OR current_monthly_hosting_cost_usd >= 0),
    CONSTRAINT ck_project_inputs_upload_size CHECK (average_upload_size_mb IS NULL OR average_upload_size_mb >= 0),
    CONSTRAINT ck_project_inputs_storage CHECK (estimated_storage_gb IS NULL OR estimated_storage_gb >= 0),
    CONSTRAINT ck_project_inputs_uptime CHECK (required_uptime IS NULL OR required_uptime BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- MySQL has no CREATE INDEX IF NOT EXISTS. Use INFORMATION_SCHEMA so this
-- installer is safe both for a clean schema and when rerun from Workbench.
SET @ddl = IF(
    EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'project_inputs'
          AND index_name = 'ix_project_inputs_website_url'
    ),
    'SELECT ''ix_project_inputs_website_url already exists'' AS installation_note',
    'CREATE INDEX ix_project_inputs_website_url ON project_inputs (website_url(191))'
);
PREPARE installer_stmt FROM @ddl;
EXECUTE installer_stmt;
DEALLOCATE PREPARE installer_stmt;

CREATE TABLE IF NOT EXISTS project_features (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    feature_code VARCHAR(80) NOT NULL,
    feature_name VARCHAR(160) NULL,
    is_required TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_feature_code (project_id, feature_code),
    KEY ix_project_features_project (project_id),
    CONSTRAINT fk_project_features_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS project_clarifications (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NULL,
    question_key VARCHAR(120) NOT NULL,
    question_text TEXT NOT NULL,
    input_type VARCHAR(40) NOT NULL,
    answer_value TEXT NULL,
    answered_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_project_clarifications_project (project_id),
    KEY ix_project_clarifications_run (analysis_run_id),
    CONSTRAINT fk_project_clarifications_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 03. ANALYSIS RUNS, JOBS & PROGRESS
-- ============================================================================

CREATE TABLE IF NOT EXISTS analysis_runs (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    job_id VARCHAR(36) NULL,
    run_number INT UNSIGNED NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    triggered_by_user_id VARCHAR(36) NULL,
    is_latest TINYINT NOT NULL DEFAULT 0,
    failure_code VARCHAR(80) NULL,
    failure_message_safe VARCHAR(500) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_analysis_runs_public_id (public_id),
    UNIQUE KEY uq_analysis_run_number (project_id, run_number),
    KEY ix_analysis_runs_project (project_id),
    KEY ix_analysis_runs_job (job_id),
    KEY ix_analysis_runs_status (status),
    KEY ix_analysis_runs_started (started_at),
    KEY ix_analysis_runs_project_latest (project_id, is_latest),
    CONSTRAINT fk_analysis_runs_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_analysis_runs_trigger_user FOREIGN KEY (triggered_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_analysis_runs_status CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    job_type VARCHAR(40) NOT NULL DEFAULT 'FULL_ANALYSIS',
    status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
    current_stage VARCHAR(60) NULL,
    progress INT NOT NULL DEFAULT 0,
    progress_percent INT GENERATED ALWAYS AS (progress) STORED,
    stages_json JSON NOT NULL,
    completed_stage_count INT UNSIGNED NOT NULL DEFAULT 0,
    total_stage_count INT UNSIGNED NOT NULL DEFAULT 11,
    queue_name VARCHAR(80) NULL,
    cancel_requested TINYINT NOT NULL DEFAULT 0,
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    last_heartbeat_at DATETIME(6) NULL,
    error_code VARCHAR(80) NULL,
    error_message VARCHAR(500) NULL,
    error_message_safe VARCHAR(500) GENERATED ALWAYS AS (error_message) STORED,
    worker_id VARCHAR(120) NULL,
    worker_reference VARCHAR(120) NULL,
    retry_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_analysis_jobs_public_id (public_id),
    KEY ix_analysis_jobs_project (project_id),
    KEY ix_analysis_jobs_run (analysis_run_id),
    KEY ix_analysis_jobs_status (status),
    KEY ix_jobs_project_status (project_id, status),
    CONSTRAINT fk_analysis_jobs_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_analysis_jobs_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_analysis_jobs_status CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED')),
    CONSTRAINT ck_analysis_jobs_progress CHECK (progress BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analysis_stage_logs (
    id VARCHAR(36) NOT NULL,
    analysis_job_id VARCHAR(36) NOT NULL,
    stage_code VARCHAR(60) NOT NULL,
    stage_name VARCHAR(120) NOT NULL,
    stage_order INT UNSIGNED NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    progress_percent INT UNSIGNED NOT NULL DEFAULT 0,
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    warning_message VARCHAR(500) NULL,
    error_code VARCHAR(80) NULL,
    error_message_safe VARCHAR(500) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_analysis_stage_order (analysis_job_id, stage_order),
    KEY ix_analysis_stage_job (analysis_job_id),
    KEY ix_analysis_stage_code (stage_code),
    CONSTRAINT fk_analysis_stage_job FOREIGN KEY (analysis_job_id) REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    CONSTRAINT ck_analysis_stage_order CHECK (stage_order > 0),
    CONSTRAINT ck_analysis_stage_progress CHECK (progress_percent BETWEEN 0 AND 100),
    CONSTRAINT ck_analysis_stage_status CHECK (status IN ('PENDING','RUNNING','COMPLETED','WARNING','FAILED','CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET @ddl = IF(
    EXISTS (
        SELECT 1 FROM information_schema.referential_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'project_clarifications'
          AND constraint_name = 'fk_project_clarifications_run'
    ),
    'SELECT ''fk_project_clarifications_run already exists'' AS installation_note',
    'ALTER TABLE project_clarifications ADD CONSTRAINT fk_project_clarifications_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL'
);
PREPARE installer_stmt FROM @ddl;
EXECUTE installer_stmt;
DEALLOCATE PREPARE installer_stmt;

-- ============================================================================
-- 04. TECHNOLOGY DETECTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS technology_detections (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    technology VARCHAR(120) NOT NULL,
    technology_name VARCHAR(120) GENERATED ALWAYS AS (technology) STORED,
    technology_version VARCHAR(80) NULL,
    category VARCHAR(60) NOT NULL,
    confidence DECIMAL(6,5) NOT NULL,
    confidence_score DECIMAL(6,5) GENERATED ALWAYS AS (confidence) STORED,
    confidence_label VARCHAR(30) NOT NULL,
    detection_status VARCHAR(30) NOT NULL DEFAULT 'DETECTED',
    is_user_confirmed TINYINT NOT NULL DEFAULT 0,
    user_correction JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_technology_project (project_id),
    KEY ix_technology_run (analysis_run_id),
    KEY ix_technology_category (category),
    KEY ix_technology_name (technology),
    CONSTRAINT fk_technology_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_technology_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_technology_confidence CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT ck_technology_confidence_label CHECK (confidence_label IN ('HIGH','MEDIUM','LOW','UNKNOWN'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS technology_evidence (
    id VARCHAR(36) NOT NULL,
    detection_id VARCHAR(36) NOT NULL,
    source VARCHAR(60) NOT NULL,
    pattern VARCHAR(255) NOT NULL,
    value_masked VARCHAR(255) NULL,
    weight DECIMAL(6,5) NOT NULL DEFAULT 1.00000,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_technology_evidence_detection (detection_id),
    CONSTRAINT fk_technology_evidence_detection FOREIGN KEY (detection_id) REFERENCES technology_detections(id) ON DELETE CASCADE,
    CONSTRAINT ck_technology_evidence_weight CHECK (weight BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS technology_feedback (
    id VARCHAR(36) NOT NULL,
    technology_detection_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    detected_technology VARCHAR(120) NOT NULL,
    actual_technology VARCHAR(120) NOT NULL,
    reason TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_technology_feedback_detection (technology_detection_id),
    KEY ix_technology_feedback_project (project_id),
    KEY ix_technology_feedback_user (user_id),
    CONSTRAINT fk_technology_feedback_detection FOREIGN KEY (technology_detection_id) REFERENCES technology_detections(id) ON DELETE RESTRICT,
    CONSTRAINT fk_technology_feedback_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_technology_feedback_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS technology_recommendations (
    id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    category VARCHAR(60) NOT NULL,
    technology_name VARCHAR(120) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    reason TEXT NOT NULL,
    is_selected TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_technology_recommendation_run (analysis_run_id),
    KEY ix_technology_recommendation_project (project_id),
    CONSTRAINT fk_technology_recommendation_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT fk_technology_recommendation_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT ck_technology_recommendation_score CHECK (score BETWEEN 0 AND 100),
    CONSTRAINT ck_technology_recommendation_category CHECK (category IN ('FRONTEND','BACKEND','DATABASE','CACHE','CDN','SUPPORTING_SERVICE','OTHER'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 05. PERFORMANCE AUDITING
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_audits (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    strategy VARCHAR(20) NOT NULL DEFAULT 'MOBILE',
    device_type VARCHAR(20) GENERATED ALWAYS AS (strategy) STORED,
    status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE',
    audit_status VARCHAR(30) GENERATED ALWAYS AS (status) STORED,
    performance_score DECIMAL(5,2) NULL,
    accessibility_score DECIMAL(5,2) NULL,
    best_practices_score DECIMAL(5,2) NULL,
    seo_score DECIMAL(5,2) NULL,
    metrics_json JSON NOT NULL,
    source VARCHAR(80) NOT NULL DEFAULT 'PageSpeed Insights',
    audit_source VARCHAR(80) GENERATED ALWAYS AS (source) STORED,
    external_audit_id VARCHAR(255) NULL,
    tested_url VARCHAR(2048) NULL,
    warning VARCHAR(500) NULL,
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    audited_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_performance_project (project_id),
    KEY ix_performance_run (analysis_run_id),
    KEY ix_performance_strategy (strategy),
    KEY ix_performance_audited (audited_at),
    KEY ix_performance_run_strategy (analysis_run_id, strategy),
    CONSTRAINT fk_performance_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_performance_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_performance_strategy CHECK (strategy IN ('MOBILE','DESKTOP')),
    CONSTRAINT ck_performance_score CHECK (performance_score IS NULL OR performance_score BETWEEN 0 AND 100),
    CONSTRAINT ck_accessibility_score CHECK (accessibility_score IS NULL OR accessibility_score BETWEEN 0 AND 100),
    CONSTRAINT ck_best_practices_score CHECK (best_practices_score IS NULL OR best_practices_score BETWEEN 0 AND 100),
    CONSTRAINT ck_seo_score CHECK (seo_score IS NULL OR seo_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS performance_metrics (
    id VARCHAR(36) NOT NULL,
    performance_audit_id VARCHAR(36) NOT NULL,
    metric_code VARCHAR(40) NOT NULL,
    metric_name VARCHAR(120) NOT NULL,
    metric_value DECIMAL(18,5) NULL,
    metric_unit VARCHAR(30) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN',
    target_value DECIMAL(18,5) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_performance_metric (performance_audit_id, metric_code),
    KEY ix_performance_metric_audit (performance_audit_id),
    KEY ix_performance_metric_code (metric_code),
    CONSTRAINT fk_performance_metric_audit FOREIGN KEY (performance_audit_id) REFERENCES performance_audits(id) ON DELETE CASCADE,
    CONSTRAINT ck_performance_metric_status CHECK (status IN ('GOOD','NEEDS_IMPROVEMENT','POOR','UNKNOWN'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 06. WORKLOAD ESTIMATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS workload_estimates (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    concurrent_users INT UNSIGNED NULL,
    requests_per_user_per_minute DECIMAL(10,4) NULL,
    estimated_requests_per_minute DECIMAL(16,4) NULL,
    estimated_rps DECIMAL(16,4) NULL,
    estimated_requests_per_second DECIMAL(16,4) GENERATED ALWAYS AS (estimated_rps) STORED,
    peak_rps DECIMAL(16,4) NULL,
    peak_requests_per_second DECIMAL(16,4) GENERATED ALWAYS AS (peak_rps) STORED,
    peak_multiplier DECIMAL(8,4) NULL,
    classification VARCHAR(30) NOT NULL,
    traffic_classification VARCHAR(30) GENERATED ALWAYS AS (classification) STORED,
    database_intensity VARCHAR(30) NULL,
    storage_gb DECIMAL(14,2) NULL,
    estimated_storage_gb DECIMAL(14,2) GENERATED ALWAYS AS (storage_gb) STORED,
    bandwidth_gb DECIMAL(16,2) NULL,
    estimated_monthly_bandwidth_gb DECIMAL(16,2) GENERATED ALWAYS AS (bandwidth_gb) STORED,
    growth_level VARCHAR(30) NULL,
    assumptions JSON NOT NULL,
    evidence_quality DECIMAL(6,5) NOT NULL DEFAULT 0.50000,
    confidence_score DECIMAL(6,5) NULL,
    confidence_label VARCHAR(30) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_workload_project (project_id),
    KEY ix_workload_run (analysis_run_id),
    KEY ix_workload_classification (classification),
    CONSTRAINT fk_workload_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_workload_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_workload_classification CHECK (classification IN ('LOW','MEDIUM','HIGH','VERY_HIGH')),
    CONSTRAINT ck_workload_evidence CHECK (evidence_quality BETWEEN 0 AND 1),
    CONSTRAINT ck_workload_confidence CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS workload_assumptions (
    id VARCHAR(36) NOT NULL,
    workload_estimate_id VARCHAR(36) NOT NULL,
    assumption_key VARCHAR(120) NOT NULL,
    assumption_value TEXT NULL,
    description TEXT NOT NULL,
    source_type VARCHAR(30) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_workload_assumptions_estimate (workload_estimate_id),
    CONSTRAINT fk_workload_assumptions_estimate FOREIGN KEY (workload_estimate_id) REFERENCES workload_estimates(id) ON DELETE CASCADE,
    CONSTRAINT ck_workload_assumption_source CHECK (source_type IN ('USER_INPUT','SYSTEM_DEFAULT','CALCULATED','ESTIMATED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 07. CLOUD PROVIDERS, HOSTING PLANS & USD PRICING
-- ============================================================================

CREATE TABLE IF NOT EXISTS cloud_providers (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    provider_code VARCHAR(60) NULL,
    website_url VARCHAR(2048) NULL,
    active TINYINT NOT NULL DEFAULT 1,
    status VARCHAR(20) GENERATED ALWAYS AS (CASE WHEN active = 1 THEN 'ACTIVE' ELSE 'INACTIVE' END) STORED,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_cloud_provider_public_id (public_id),
    UNIQUE KEY uq_cloud_provider_name (name),
    UNIQUE KEY uq_cloud_provider_slug (slug),
    UNIQUE KEY uq_cloud_provider_code (provider_code),
    KEY ix_cloud_provider_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS hosting_plans (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    provider_id VARCHAR(36) NOT NULL,
    plan_code VARCHAR(120) NULL,
    plan_name VARCHAR(160) NOT NULL,
    architecture_type VARCHAR(30) NOT NULL,
    region VARCHAR(80) NOT NULL,
    region_code VARCHAR(80) NULL,
    region_name VARCHAR(120) NULL,
    vcpu INT UNSIGNED NOT NULL,
    ram_gb DECIMAL(10,2) NOT NULL,
    storage_gb DECIMAL(12,2) NOT NULL,
    bandwidth_gb DECIMAL(14,2) NULL,
    managed TINYINT NOT NULL DEFAULT 0,
    high_availability_supported TINYINT NOT NULL DEFAULT 0,
    autoscaling_supported TINYINT NOT NULL DEFAULT 0,
    base_monthly_cost DECIMAL(12,2) NOT NULL,
    base_monthly_price_usd DECIMAL(12,2) GENERATED ALWAYS AS (base_monthly_cost) STORED,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    source VARCHAR(255) NOT NULL DEFAULT 'APPLICATION_MANAGED',
    active TINYINT NOT NULL DEFAULT 1,
    is_demo TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_hosting_plan_public_id (public_id),
    UNIQUE KEY uq_hosting_plan_code (provider_id, plan_code, region),
    KEY ix_hosting_provider (provider_id),
    KEY ix_hosting_architecture (architecture_type),
    KEY ix_hosting_region (region),
    KEY ix_hosting_active (active),
    KEY ix_hosting_provider_region (provider_id, region),
    CONSTRAINT fk_hosting_plan_provider FOREIGN KEY (provider_id) REFERENCES cloud_providers(id) ON DELETE RESTRICT,
    CONSTRAINT ck_hosting_architecture CHECK (architecture_type IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_hosting_currency CHECK (currency = 'USD'),
    CONSTRAINT ck_hosting_base_cost CHECK (base_monthly_cost >= 0),
    CONSTRAINT ck_hosting_resources CHECK (vcpu > 0 AND ram_gb > 0 AND storage_gb >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pricing_snapshots (
    id VARCHAR(36) NOT NULL,
    hosting_plan_id VARCHAR(36) NOT NULL,
    min_monthly_cost DECIMAL(12,2) NOT NULL,
    max_monthly_cost DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    components JSON NOT NULL,
    compute_price_usd DECIMAL(12,2) NULL,
    database_price_usd DECIMAL(12,2) NULL,
    storage_price_usd DECIMAL(12,2) NULL,
    bandwidth_price_usd DECIMAL(12,2) NULL,
    backup_price_usd DECIMAL(12,2) NULL,
    monitoring_price_usd DECIMAL(12,2) NULL,
    cdn_price_usd DECIMAL(12,2) NULL,
    estimated_min_monthly_usd DECIMAL(12,2) GENERATED ALWAYS AS (min_monthly_cost) STORED,
    estimated_max_monthly_usd DECIMAL(12,2) GENERATED ALWAYS AS (max_monthly_cost) STORED,
    source VARCHAR(255) NOT NULL,
    pricing_source VARCHAR(255) GENERATED ALWAYS AS (source) STORED,
    source_reference VARCHAR(1024) NULL,
    effective_date DATE NULL,
    captured_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    is_current TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_pricing_plan (hosting_plan_id),
    KEY ix_pricing_captured (captured_at),
    KEY ix_pricing_current (hosting_plan_id, is_current),
    CONSTRAINT fk_pricing_plan FOREIGN KEY (hosting_plan_id) REFERENCES hosting_plans(id) ON DELETE RESTRICT,
    CONSTRAINT ck_pricing_currency CHECK (currency = 'USD'),
    CONSTRAINT ck_pricing_range CHECK (min_monthly_cost >= 0 AND max_monthly_cost >= min_monthly_cost),
    CONSTRAINT ck_pricing_compute CHECK (compute_price_usd IS NULL OR compute_price_usd >= 0),
    CONSTRAINT ck_pricing_database CHECK (database_price_usd IS NULL OR database_price_usd >= 0),
    CONSTRAINT ck_pricing_storage CHECK (storage_price_usd IS NULL OR storage_price_usd >= 0),
    CONSTRAINT ck_pricing_bandwidth CHECK (bandwidth_price_usd IS NULL OR bandwidth_price_usd >= 0),
    CONSTRAINT ck_pricing_backup CHECK (backup_price_usd IS NULL OR backup_price_usd >= 0),
    CONSTRAINT ck_pricing_monitoring CHECK (monitoring_price_usd IS NULL OR monitoring_price_usd >= 0),
    CONSTRAINT ck_pricing_cdn CHECK (cdn_price_usd IS NULL OR cdn_price_usd >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 08. ML DATASETS, MODEL MANAGEMENT & PREDICTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_datasets (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(512) NOT NULL,
    file_hash VARCHAR(128) NOT NULL,
    row_count BIGINT UNSIGNED NULL,
    validation_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    uploaded_by_user_id VARCHAR(36) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_ml_dataset_public_id (public_id),
    UNIQUE KEY uq_ml_dataset_hash (file_hash),
    KEY ix_ml_dataset_user (uploaded_by_user_id),
    KEY ix_ml_dataset_validation (validation_status),
    CONSTRAINT fk_ml_dataset_user FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ml_dataset_validation_results (
    id VARCHAR(36) NOT NULL,
    dataset_id VARCHAR(36) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    column_name VARCHAR(160) NULL,
    issue_code VARCHAR(80) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_dataset_validation_dataset (dataset_id),
    KEY ix_dataset_validation_severity (severity),
    CONSTRAINT fk_dataset_validation_dataset FOREIGN KEY (dataset_id) REFERENCES ml_datasets(id) ON DELETE CASCADE,
    CONSTRAINT ck_dataset_validation_severity CHECK (severity IN ('INFO','WARNING','ERROR'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ml_model_versions (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    model_name VARCHAR(120) NULL,
    version VARCHAR(60) NOT NULL,
    algorithm VARCHAR(120) NOT NULL,
    model_type VARCHAR(60) NOT NULL DEFAULT 'HOSTING_CLASSIFIER',
    training_rows INT NOT NULL,
    training_dataset_name VARCHAR(255) NULL,
    dataset_id VARCHAR(36) NULL,
    feature_schema JSON NOT NULL,
    label_schema_json JSON NULL,
    accuracy DECIMAL(6,5) NULL,
    `precision` DECIMAL(6,5) NULL,
    recall DECIMAL(6,5) NULL,
    f1 DECIMAL(6,5) NULL,
    confusion_matrix JSON NOT NULL,
    class_distribution JSON NOT NULL,
    feature_importance JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    trained_at DATETIME(6) NULL,
    activated_at DATETIME(6) NULL,
    archived_at DATETIME(6) NULL,
    is_active TINYINT NOT NULL DEFAULT 0,
    model_path VARCHAR(255) NOT NULL,
    artifact_path VARCHAR(255) GENERATED ALWAYS AS (model_path) STORED,
    PRIMARY KEY (id),
    UNIQUE KEY uq_ml_model_public_id (public_id),
    UNIQUE KEY uq_ml_model_version (version),
    KEY ix_ml_model_active (is_active),
    KEY ix_ml_model_type (model_type),
    KEY ix_ml_model_dataset (dataset_id),
    CONSTRAINT fk_ml_model_dataset FOREIGN KEY (dataset_id) REFERENCES ml_datasets(id) ON DELETE SET NULL,
    CONSTRAINT ck_ml_model_accuracy CHECK (accuracy IS NULL OR accuracy BETWEEN 0 AND 1),
    CONSTRAINT ck_ml_model_precision CHECK (`precision` IS NULL OR `precision` BETWEEN 0 AND 1),
    CONSTRAINT ck_ml_model_recall CHECK (recall IS NULL OR recall BETWEEN 0 AND 1),
    CONSTRAINT ck_ml_model_f1 CHECK (f1 IS NULL OR f1 BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Canonical training-job table name used by the supplied backend ORM.
CREATE TABLE IF NOT EXISTS model_training_jobs (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    user_id VARCHAR(36) NOT NULL,
    requested_by_user_id VARCHAR(36) GENERATED ALWAYS AS (user_id) STORED,
    model_type VARCHAR(60) NOT NULL DEFAULT 'HOSTING_CLASSIFIER',
    status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
    current_stage VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
    progress INT NOT NULL DEFAULT 0,
    progress_percent INT GENERATED ALWAYS AS (progress) STORED,
    dataset_path VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(36) NULL,
    dataset_filename VARCHAR(255) NULL,
    dataset_row_count BIGINT UNSIGNED NULL,
    result_model_id VARCHAR(36) NULL,
    created_model_version_id VARCHAR(36) NULL,
    error_code VARCHAR(80) NULL,
    error_message VARCHAR(500) NULL,
    error_message_safe VARCHAR(500) GENERATED ALWAYS AS (error_message) STORED,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_model_training_job_public_id (public_id),
    KEY ix_model_training_user (user_id),
    KEY ix_model_training_status (status),
    KEY ix_model_training_dataset (dataset_id),
    KEY ix_model_training_result_model (result_model_id),
    CONSTRAINT fk_model_training_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_model_training_dataset FOREIGN KEY (dataset_id) REFERENCES ml_datasets(id) ON DELETE SET NULL,
    CONSTRAINT fk_model_training_result FOREIGN KEY (result_model_id) REFERENCES ml_model_versions(id) ON DELETE SET NULL,
    CONSTRAINT ck_model_training_progress CHECK (progress BETWEEN 0 AND 100),
    CONSTRAINT ck_model_training_status CHECK (status IN ('QUEUED','RUNNING','VALIDATING','PREPROCESSING','TRAINING','EVALUATING','SAVING','COMPLETED','FAILED','CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ml_evaluation_metrics (
    id VARCHAR(36) NOT NULL,
    model_version_id VARCHAR(36) NOT NULL,
    metric_name VARCHAR(120) NOT NULL,
    metric_value DECIMAL(12,6) NULL,
    class_name VARCHAR(120) NULL,
    metadata_json JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_ml_evaluation_model (model_version_id),
    KEY ix_ml_evaluation_metric (metric_name),
    CONSTRAINT fk_ml_evaluation_model FOREIGN KEY (model_version_id) REFERENCES ml_model_versions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS model_predictions (
    id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NULL,
    model_version_id VARCHAR(36) NULL,
    predicted_class VARCHAR(30) NOT NULL,
    prediction_confidence DECIMAL(6,5) NULL,
    probabilities JSON NOT NULL,
    features JSON NOT NULL,
    input_feature_snapshot_json JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_model_predictions_run (analysis_run_id),
    KEY ix_model_predictions_project (project_id),
    KEY ix_model_predictions_version (model_version_id),
    CONSTRAINT fk_model_predictions_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT fk_model_predictions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_model_predictions_version FOREIGN KEY (model_version_id) REFERENCES ml_model_versions(id) ON DELETE SET NULL,
    CONSTRAINT ck_model_prediction_class CHECK (predicted_class IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_model_prediction_confidence CHECK (prediction_confidence IS NULL OR prediction_confidence BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS model_prediction_probabilities (
    id VARCHAR(36) NOT NULL,
    model_prediction_id VARCHAR(36) NOT NULL,
    hosting_type VARCHAR(30) NOT NULL,
    probability DECIMAL(6,5) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_model_prediction_probability (model_prediction_id, hosting_type),
    KEY ix_model_prediction_probability_prediction (model_prediction_id),
    CONSTRAINT fk_model_prediction_probability_prediction FOREIGN KEY (model_prediction_id) REFERENCES model_predictions(id) ON DELETE CASCADE,
    CONSTRAINT ck_model_probability_hosting CHECK (hosting_type IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_model_probability_value CHECK (probability BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 09. RECOMMENDATION ENGINE - ALL REQUESTED RECOMMENDATION STRUCTURES
-- ============================================================================

CREATE TABLE IF NOT EXISTS recommendation_rule_results (
    id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    rule_code VARCHAR(100) NOT NULL,
    rule_name VARCHAR(180) NULL,
    hosting_type VARCHAR(30) NOT NULL,
    effect_type VARCHAR(30) NOT NULL,
    score_delta DECIMAL(8,3) NOT NULL DEFAULT 0,
    triggered TINYINT NOT NULL DEFAULT 1,
    reason TEXT NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_recommendation_rule_run (analysis_run_id),
    KEY ix_recommendation_rule_project (project_id),
    KEY ix_recommendation_rule_hosting (hosting_type),
    CONSTRAINT fk_recommendation_rule_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT fk_recommendation_rule_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT ck_recommendation_rule_hosting CHECK (hosting_type IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_recommendation_rule_effect CHECK (effect_type IN ('BONUS','PENALTY','BLOCK','INFORMATION'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    model_prediction_id VARCHAR(36) NULL,

    -- Exact backend fields
    recommended_option VARCHAR(30) NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    confidence_value DECIMAL(6,5) NOT NULL,
    confidence_label VARCHAR(30) NOT NULL,
    resource_size JSON NOT NULL,
    estimated_cost JSON NOT NULL,
    alternatives JSON NOT NULL,
    reasons JSON NOT NULL,
    assumptions JSON NOT NULL,
    warnings JSON NOT NULL,
    rule_results JSON NOT NULL,
    model_version VARCHAR(60) NULL,
    model_probabilities JSON NOT NULL,

    -- Advanced relational/API aliases; automatically derived where possible.
    recommended_hosting_type VARCHAR(30) GENERATED ALWAYS AS (recommended_option) STORED,
    confidence_score DECIMAL(6,5) GENERATED ALWAYS AS (confidence_value) STORED,
    estimated_min_monthly_cost_usd DECIMAL(12,2)
      GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.min')) AS DECIMAL(12,2))) STORED,
    estimated_max_monthly_cost_usd DECIMAL(12,2)
      GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.max')) AS DECIMAL(12,2))) STORED,
    pricing_snapshot_date DATETIME(6) NULL,
    user_preferred_hosting_type VARCHAR(30) NULL,
    is_current TINYINT NOT NULL DEFAULT 1,
    is_stale TINYINT NOT NULL DEFAULT 0,
    recommendation_engine_version VARCHAR(60) NULL,
    scoring_config_version VARCHAR(60) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_recommendations_public_id (public_id),
    UNIQUE KEY uq_recommendations_analysis_run (analysis_run_id),
    KEY ix_recommendations_project (project_id),
    KEY ix_recommendations_option (recommended_option),
    KEY ix_recommendations_current (project_id, is_current),
    KEY ix_recommendations_model_prediction (model_prediction_id),
    CONSTRAINT fk_recommendations_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_recommendations_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE RESTRICT,
    CONSTRAINT fk_recommendations_prediction FOREIGN KEY (model_prediction_id) REFERENCES model_predictions(id) ON DELETE SET NULL,
    CONSTRAINT ck_recommendations_option CHECK (recommended_option IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_recommendations_score CHECK (overall_score BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendations_confidence CHECK (confidence_value BETWEEN 0 AND 1),
    CONSTRAINT ck_recommendations_confidence_label CHECK (confidence_label IN ('HIGH','MEDIUM','LOW','INSUFFICIENT_DATA')),
    CONSTRAINT ck_recommendations_cost_range CHECK (
        (estimated_min_monthly_cost_usd IS NULL AND estimated_max_monthly_cost_usd IS NULL)
        OR (estimated_min_monthly_cost_usd >= 0 AND estimated_max_monthly_cost_usd >= estimated_min_monthly_cost_usd)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendation_scores (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    `option` VARCHAR(30) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    ml_probability DECIMAL(6,5) NOT NULL DEFAULT 0.00000,
    budget_fit DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    traffic_fit DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    scalability_fit DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    reliability_fit DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    operational_fit DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    complexity_score DECIMAL(5,2) NULL,
    performance_fit_score DECIMAL(5,2) NULL,
    is_recommended TINYINT NOT NULL DEFAULT 0,
    rule_adjustments JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_recommendation_score_option (recommendation_id, `option`),
    KEY ix_recommendation_scores_recommendation (recommendation_id),
    CONSTRAINT fk_recommendation_scores_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_recommendation_scores_option CHECK (`option` IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_recommendation_scores_score CHECK (score BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendation_scores_ml CHECK (ml_probability BETWEEN 0 AND 1),
    CONSTRAINT ck_recommendation_scores_budget CHECK (budget_fit BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendation_scores_traffic CHECK (traffic_fit BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendation_scores_scalability CHECK (scalability_fit BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendation_scores_reliability CHECK (reliability_fit BETWEEN 0 AND 100),
    CONSTRAINT ck_recommendation_scores_operational CHECK (operational_fit BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendation_reasons (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    hosting_type VARCHAR(30) NOT NULL,
    reason_type VARCHAR(30) NOT NULL,
    title VARCHAR(180) NOT NULL,
    description TEXT NOT NULL,
    importance VARCHAR(30) NULL,
    display_order INT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_recommendation_reasons_recommendation (recommendation_id),
    KEY ix_recommendation_reasons_type (reason_type),
    CONSTRAINT fk_recommendation_reasons_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_recommendation_reasons_hosting CHECK (hosting_type IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_recommendation_reasons_type CHECK (reason_type IN ('POSITIVE','NEGATIVE','WARNING','INFORMATION')),
    CONSTRAINT ck_recommendation_reasons_order CHECK (display_order > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendation_assumptions (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    assumption_key VARCHAR(120) NOT NULL,
    assumption_value TEXT NULL,
    description TEXT NOT NULL,
    confidence_impact DECIMAL(8,5) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_recommendation_assumptions_recommendation (recommendation_id),
    CONSTRAINT fk_recommendation_assumptions_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendation_confidence_factors (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    factor_code VARCHAR(80) NOT NULL,
    factor_score DECIMAL(6,5) NOT NULL,
    weight DECIMAL(6,5) NOT NULL,
    weighted_score DECIMAL(8,6) NOT NULL,
    reason TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_recommendation_confidence_factor (recommendation_id, factor_code),
    KEY ix_recommendation_confidence_recommendation (recommendation_id),
    CONSTRAINT fk_recommendation_confidence_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_recommendation_confidence_score CHECK (factor_score BETWEEN 0 AND 1),
    CONSTRAINT ck_recommendation_confidence_weight CHECK (weight BETWEEN 0 AND 1),
    CONSTRAINT ck_recommendation_confidence_factor CHECK (factor_code IN ('ML_CERTAINTY','INPUT_COMPLETENESS','TECHNOLOGY_EVIDENCE','PERFORMANCE_EVIDENCE','WORKLOAD_QUALITY','PRICING_FRESHNESS'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommended_resources (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    vcpu INT UNSIGNED NOT NULL,
    ram_gb DECIMAL(10,2) NOT NULL,
    storage_gb DECIMAL(12,2) NOT NULL,
    bandwidth_gb DECIMAL(14,2) NULL,
    database_strategy VARCHAR(255) NULL,
    managed_database_recommended TINYINT NULL,
    cdn_recommended TINYINT NULL,
    backup_strategy VARCHAR(255) NULL,
    monitoring_recommended TINYINT NULL,
    autoscaling_strategy VARCHAR(255) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_recommended_resources_recommendation (recommendation_id),
    CONSTRAINT fk_recommended_resources_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_recommended_resources_values CHECK (vcpu > 0 AND ram_gb > 0 AND storage_gb >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cost_estimates (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    hosting_type VARCHAR(30) NOT NULL,
    compute_min_usd DECIMAL(12,2) NULL,
    compute_max_usd DECIMAL(12,2) NULL,
    database_min_usd DECIMAL(12,2) NULL,
    database_max_usd DECIMAL(12,2) NULL,
    storage_min_usd DECIMAL(12,2) NULL,
    storage_max_usd DECIMAL(12,2) NULL,
    bandwidth_min_usd DECIMAL(12,2) NULL,
    bandwidth_max_usd DECIMAL(12,2) NULL,
    backup_min_usd DECIMAL(12,2) NULL,
    backup_max_usd DECIMAL(12,2) NULL,
    monitoring_min_usd DECIMAL(12,2) NULL,
    monitoring_max_usd DECIMAL(12,2) NULL,
    cdn_min_usd DECIMAL(12,2) NULL,
    cdn_max_usd DECIMAL(12,2) NULL,
    total_min_usd DECIMAL(12,2) NULL,
    total_max_usd DECIMAL(12,2) NULL,
    current_cost_usd DECIMAL(12,2) NULL,
    potential_saving_min_usd DECIMAL(12,2) NULL,
    potential_saving_max_usd DECIMAL(12,2) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_cost_estimate_option (recommendation_id, hosting_type),
    KEY ix_cost_estimate_recommendation (recommendation_id),
    CONSTRAINT fk_cost_estimate_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_cost_estimate_hosting CHECK (hosting_type IN ('VPS','CLOUD_VM','KUBERNETES')),
    CONSTRAINT ck_cost_estimate_total CHECK (total_min_usd IS NULL OR total_min_usd >= 0),
    CONSTRAINT ck_cost_estimate_total_max CHECK (total_max_usd IS NULL OR total_max_usd >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cost_estimate_components (
    id VARCHAR(36) NOT NULL,
    cost_estimate_id VARCHAR(36) NOT NULL,
    component_code VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL,
    min_usd DECIMAL(12,2) NULL,
    max_usd DECIMAL(12,2) NULL,
    explanation TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_cost_estimate_component (cost_estimate_id, component_code),
    CONSTRAINT fk_cost_component_estimate FOREIGN KEY (cost_estimate_id) REFERENCES cost_estimates(id) ON DELETE CASCADE,
    CONSTRAINT ck_cost_component_status CHECK (status IN ('UNKNOWN','INCLUDED','ESTIMATED','NOT_REQUIRED')),
    CONSTRAINT ck_cost_component_min CHECK (min_usd IS NULL OR min_usd >= 0),
    CONSTRAINT ck_cost_component_max CHECK (max_usd IS NULL OR max_usd >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS architecture_nodes (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    node_key VARCHAR(120) NOT NULL,
    node_type VARCHAR(40) NOT NULL,
    label VARCHAR(160) NOT NULL,
    description TEXT NULL,
    position_x DECIMAL(12,3) NULL,
    position_y DECIMAL(12,3) NULL,
    display_order INT UNSIGNED NOT NULL DEFAULT 1,
    metadata_json JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_architecture_node_key (recommendation_id, node_key),
    KEY ix_architecture_nodes_recommendation (recommendation_id),
    CONSTRAINT fk_architecture_nodes_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_architecture_node_type CHECK (node_type IN ('CLIENT','DNS','CDN','LOAD_BALANCER','WEB_SERVER','APPLICATION','API','DATABASE','CACHE','OBJECT_STORAGE','MONITORING','BACKUP','KUBERNETES','OTHER'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS architecture_edges (
    id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NOT NULL,
    source_node_key VARCHAR(120) NOT NULL,
    target_node_key VARCHAR(120) NOT NULL,
    edge_label VARCHAR(160) NULL,
    display_order INT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_architecture_edges_recommendation (recommendation_id),
    CONSTRAINT fk_architecture_edges_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    CONSTRAINT ck_architecture_edge_nodes CHECK (source_node_key <> target_node_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 10. OPTIMIZATION ENGINE
-- ============================================================================

CREATE TABLE IF NOT EXISTS optimization_suggestions (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    category VARCHAR(40) NOT NULL,
    title VARCHAR(180) NOT NULL,
    explanation TEXT NOT NULL,
    description TEXT NULL,
    impact VARCHAR(160) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    benefit VARCHAR(180) NOT NULL,
    recommended_action TEXT NULL,
    expected_benefit TEXT NULL,
    source_metric VARCHAR(80) NULL,
    source_value VARCHAR(120) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    completed_at DATETIME(6) NULL,
    display_order INT UNSIGNED NOT NULL DEFAULT 1,
    steps JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_optimization_public_id (public_id),
    KEY ix_optimization_project (project_id),
    KEY ix_optimization_run (analysis_run_id),
    KEY ix_optimization_priority (priority),
    KEY ix_optimization_category (category),
    KEY ix_optimization_status (status),
    CONSTRAINT fk_optimization_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_optimization_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_optimization_priority CHECK (priority IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    CONSTRAINT ck_optimization_category CHECK (category IN ('FRONTEND','BACKEND','DATABASE','CACHE_CDN','HOSTING','SECURITY','MONITORING','SCALABILITY','COST')),
    CONSTRAINT ck_optimization_difficulty CHECK (difficulty IN ('EASY','MEDIUM','HARD')),
    CONSTRAINT ck_optimization_status CHECK (status IN ('OPEN','DONE','NOT_RELEVANT'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 11. SAFE k6 LOAD-TEST PLANNING
-- ============================================================================

CREATE TABLE IF NOT EXISTS load_test_plans (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NULL,
    test_type VARCHAR(20) NOT NULL,
    virtual_users INT UNSIGNED NOT NULL,
    duration_seconds INT UNSIGNED NOT NULL,
    target_url VARCHAR(2048) NOT NULL,
    authorization_confirmed TINYINT NULL,
    risk_acknowledged TINYINT NULL,
    response_time_threshold_ms INT UNSIGNED NOT NULL DEFAULT 2000,
    error_rate_threshold DECIMAL(8,6) NOT NULL DEFAULT 0.010000,
    stages JSON NOT NULL,
    script LONGTEXT NOT NULL,
    file_key VARCHAR(255) NULL,
    script_filename VARCHAR(255) NULL,
    safety_notes JSON NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'GENERATED',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_load_test_public_id (public_id),
    KEY ix_load_test_project (project_id),
    KEY ix_load_test_user (user_id),
    KEY ix_load_test_run (analysis_run_id),
    CONSTRAINT fk_load_test_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_load_test_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_load_test_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL,
    CONSTRAINT ck_load_test_type CHECK (test_type IN ('SMOKE','LOAD','STRESS','SPIKE','SOAK')),
    CONSTRAINT ck_load_test_values CHECK (virtual_users > 0 AND duration_seconds > 0),
    CONSTRAINT ck_load_test_error_rate CHECK (error_rate_threshold BETWEEN 0 AND 1),
    CONSTRAINT ck_load_test_status CHECK (status IN ('DRAFT','GENERATED','DOWNLOADED','ARCHIVED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS load_test_stages (
    id VARCHAR(36) NOT NULL,
    load_test_plan_id VARCHAR(36) NOT NULL,
    stage_order INT UNSIGNED NOT NULL,
    duration_seconds INT UNSIGNED NOT NULL,
    target_virtual_users INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_load_test_stage_order (load_test_plan_id, stage_order),
    KEY ix_load_test_stage_plan (load_test_plan_id),
    CONSTRAINT fk_load_test_stage_plan FOREIGN KEY (load_test_plan_id) REFERENCES load_test_plans(id) ON DELETE CASCADE,
    CONSTRAINT ck_load_test_stage_order CHECK (stage_order > 0),
    CONSTRAINT ck_load_test_stage_values CHECK (duration_seconds > 0 AND target_virtual_users >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 12. REPORTS & IMMUTABLE VERSION HISTORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NOT NULL,
    recommendation_id VARCHAR(36) NULL,
    report_title VARCHAR(255) NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    latest_version_number INT UNSIGNED GENERATED ALWAYS AS (version) STORED,
    status VARCHAR(30) NOT NULL DEFAULT 'READY',
    snapshot JSON NOT NULL,
    file_key VARCHAR(255) NULL,
    generated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reports_public_id (public_id),
    UNIQUE KEY uq_report_project_version (project_id, version),
    KEY ix_reports_project (project_id),
    KEY ix_reports_user (user_id),
    KEY ix_reports_run (analysis_run_id),
    KEY ix_reports_recommendation (recommendation_id),
    KEY ix_reports_generated (generated_at),
    CONSTRAINT fk_reports_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reports_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reports_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE SET NULL,
    CONSTRAINT ck_reports_status CHECK (status IN ('GENERATING','READY','FAILED','DELETED')),
    CONSTRAINT ck_reports_version CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET @ddl = IF(
    EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'reports'
          AND index_name = 'ix_reports_title'
    ),
    'SELECT ''ix_reports_title already exists'' AS installation_note',
    'CREATE INDEX ix_reports_title ON reports (report_title)'
);
PREPARE installer_stmt FROM @ddl;
EXECUTE installer_stmt;
DEALLOCATE PREPARE installer_stmt;

CREATE TABLE IF NOT EXISTS report_versions (
    id VARCHAR(36) NOT NULL,
    report_id VARCHAR(36) NOT NULL,
    version_number INT UNSIGNED NOT NULL,
    executive_summary LONGTEXT NULL,
    report_snapshot_json JSON NOT NULL,
    html_storage_key VARCHAR(512) NULL,
    pdf_storage_key VARCHAR(512) NULL,
    model_version VARCHAR(60) NULL,
    pricing_snapshot_date DATETIME(6) NULL,
    generated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_report_version_number (report_id, version_number),
    KEY ix_report_versions_report (report_id),
    KEY ix_report_versions_generated (generated_at),
    CONSTRAINT fk_report_versions_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    CONSTRAINT ck_report_versions_version CHECK (version_number > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 13. NOTIFICATIONS, UAT, TESTING, HISTORY & AUDIT
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) NOT NULL,
    public_id VARCHAR(36) GENERATED ALWAYS AS (id) STORED,
    user_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NULL,
    type VARCHAR(40) NOT NULL,
    title VARCHAR(160) NOT NULL,
    message VARCHAR(500) NOT NULL,
    action_url VARCHAR(1024) NULL,
    is_read TINYINT NOT NULL DEFAULT 0,
    read_at DATETIME(6) NULL,
    data JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_notifications_public_id (public_id),
    KEY ix_notifications_user (user_id),
    KEY ix_notifications_project (project_id),
    KEY ix_notifications_user_read (user_id, is_read),
    KEY ix_notifications_user_created (user_id, created_at),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_feedback (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    analysis_run_id VARCHAR(36) NULL,
    recommendation_id VARCHAR(36) NULL,
    clarity_rating INT NOT NULL,
    usefulness_rating INT NOT NULL,
    ease_of_use_rating INT NOT NULL,
    recommendation_trust_rating INT NOT NULL,
    comments TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_feedback_user (user_id),
    KEY ix_feedback_project (project_id),
    KEY ix_feedback_run (analysis_run_id),
    KEY ix_feedback_recommendation (recommendation_id),
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_feedback_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_feedback_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL,
    CONSTRAINT fk_feedback_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE SET NULL,
    CONSTRAINT ck_feedback_clarity CHECK (clarity_rating BETWEEN 1 AND 5),
    CONSTRAINT ck_feedback_usefulness CHECK (usefulness_rating BETWEEN 1 AND 5),
    CONSTRAINT ck_feedback_ease CHECK (ease_of_use_rating BETWEEN 1 AND 5),
    CONSTRAINT ck_feedback_trust CHECK (recommendation_trust_rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test_results (
    id VARCHAR(36) NOT NULL,
    test_type VARCHAR(10) NOT NULL,
    test_category VARCHAR(80) NULL,
    test_name VARCHAR(180) NOT NULL,
    status VARCHAR(30) NOT NULL,
    executed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    duration_ms INT NULL,
    environment VARCHAR(80) NULL,
    reference VARCHAR(255) NULL,
    details JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_test_results_type (test_type),
    KEY ix_test_results_status (status),
    KEY ix_test_results_executed (executed_at),
    CONSTRAINT ck_test_results_type CHECK (test_type IN ('UT','IT','ST','UAT','ORT')),
    CONSTRAINT ck_test_results_status CHECK (status IN ('PASSED','FAILED','SKIPPED','NOT_RUN')),
    CONSTRAINT ck_test_results_duration CHECK (duration_ms IS NULL OR duration_ms >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS project_activity_history (
    id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    analysis_run_id VARCHAR(36) NULL,
    activity_type VARCHAR(80) NOT NULL,
    title VARCHAR(180) NOT NULL,
    description TEXT NULL,
    metadata_json JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_activity_project (project_id),
    KEY ix_activity_user (user_id),
    KEY ix_activity_run (analysis_run_id),
    KEY ix_activity_created (created_at),
    CONSTRAINT fk_activity_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_activity_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) NOT NULL,
    actor_user_id VARCHAR(36) NULL,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80) NULL,
    entity_id VARCHAR(80) NULL,
    request_id VARCHAR(120) NULL,
    ip_masked VARCHAR(80) NULL,
    old_values_json JSON NULL,
    new_values_json JSON NULL,
    metadata_json JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_audit_actor (actor_user_id),
    KEY ix_audit_action (action),
    KEY ix_audit_created (created_at),
    KEY ix_audit_entity (entity_type, entity_id),
    KEY ix_audit_request (request_id),
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 14. SYSTEM SETTINGS / NON-SECRET RECOMMENDATION CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_settings (
    id VARCHAR(36) NOT NULL,
    setting_key VARCHAR(120) NOT NULL,
    setting_value VARCHAR(1000) NOT NULL,
    data_type VARCHAR(30) NOT NULL DEFAULT 'STRING',
    description VARCHAR(500) NULL,
    is_public TINYINT NOT NULL DEFAULT 0,
    config_version VARCHAR(60) NULL,
    updated_by_user_id VARCHAR(36) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_system_setting_key (setting_key),
    KEY ix_system_setting_public (is_public),
    CONSTRAINT fk_system_setting_user FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_system_setting_type CHECK (data_type IN ('STRING','INTEGER','DECIMAL','BOOLEAN','JSON'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add circular/latest-analysis FK only after analysis_runs exists.
SET @ddl = IF(
    EXISTS (
        SELECT 1 FROM information_schema.referential_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'projects'
          AND constraint_name = 'fk_projects_latest_analysis_run'
    ),
    'SELECT ''fk_projects_latest_analysis_run already exists'' AS installation_note',
    'ALTER TABLE projects ADD CONSTRAINT fk_projects_latest_analysis_run FOREIGN KEY (latest_analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL'
);
PREPARE installer_stmt FROM @ddl;
EXECUTE installer_stmt;
DEALLOCATE PREPARE installer_stmt;

-- analysis_runs.job_id is retained for backend compatibility. It is intentionally
-- not FK-constrained because analysis_jobs.analysis_run_id already defines the
-- canonical relationship and the backend fills run.job_id after job creation.

-- ============================================================================
-- 15. VIEWS FOR DASHBOARD, CURRENT PRICING, CURRENT RECOMMENDATION & HISTORY
-- ============================================================================

CREATE OR REPLACE VIEW vw_current_hosting_prices AS
SELECT
    hp.id AS hosting_plan_id,
    hp.public_id AS hosting_plan_public_id,
    cp.id AS provider_id,
    cp.name AS provider_name,
    cp.slug AS provider_slug,
    hp.plan_name,
    hp.architecture_type,
    hp.region,
    hp.vcpu,
    hp.ram_gb,
    hp.storage_gb,
    hp.bandwidth_gb,
    hp.managed,
    hp.high_availability_supported,
    hp.autoscaling_supported,
    ranked.min_monthly_cost,
    ranked.max_monthly_cost,
    'USD' AS currency,
    ranked.components,
    ranked.source,
    ranked.source_reference,
    ranked.captured_at
FROM hosting_plans hp
JOIN cloud_providers cp ON cp.id = hp.provider_id
JOIN (
    SELECT ps.*,
           ROW_NUMBER() OVER (PARTITION BY ps.hosting_plan_id ORDER BY ps.captured_at DESC, ps.id DESC) AS rn
    FROM pricing_snapshots ps
) ranked ON ranked.hosting_plan_id = hp.id AND ranked.rn = 1
WHERE hp.active = 1 AND cp.active = 1;

CREATE OR REPLACE VIEW vw_latest_project_analysis AS
SELECT
    p.id AS project_id,
    p.user_id,
    p.title,
    p.mode,
    p.status AS project_status,
    p.latest_analysis_run_id,
    ar.status AS analysis_status,
    ar.started_at,
    ar.completed_at,
    ar.created_at AS analysis_created_at
FROM projects p
LEFT JOIN analysis_runs ar ON ar.id = p.latest_analysis_run_id
WHERE p.deleted_at IS NULL;

CREATE OR REPLACE VIEW vw_current_recommendations AS
SELECT
    r.*,
    p.user_id,
    p.title AS project_title,
    p.mode AS project_mode,
    p.recommendation_stale AS project_recommendation_stale
FROM recommendations r
JOIN projects p ON p.id = r.project_id
WHERE p.deleted_at IS NULL
  AND p.latest_analysis_run_id = r.analysis_run_id;

CREATE OR REPLACE VIEW vw_user_project_summary AS
SELECT
    p.user_id,
    p.id AS project_id,
    p.title,
    p.mode,
    p.status,
    p.website_url,
    p.target_region,
    p.created_at,
    p.updated_at,
    r.recommended_option,
    r.overall_score,
    r.confidence_value,
    r.confidence_label,
    r.estimated_min_monthly_cost_usd,
    r.estimated_max_monthly_cost_usd,
    pa.performance_score AS mobile_performance_score,
    p.recommendation_stale
FROM projects p
LEFT JOIN recommendations r
    ON r.analysis_run_id = p.latest_analysis_run_id
LEFT JOIN performance_audits pa
    ON pa.analysis_run_id = p.latest_analysis_run_id
   AND pa.strategy = 'MOBILE'
WHERE p.deleted_at IS NULL;

CREATE OR REPLACE VIEW vw_project_dashboard_summary AS
SELECT
    u.id AS user_id,
    (SELECT COUNT(*) FROM projects p
      WHERE p.user_id=u.id AND p.deleted_at IS NULL) AS total_projects,
    (SELECT COUNT(*) FROM analysis_runs ar
      JOIN projects p ON p.id=ar.project_id
      WHERE p.user_id=u.id AND p.deleted_at IS NULL AND ar.status='COMPLETED') AS completed_analyses,
    (SELECT ROUND(AVG(pa.performance_score),2) FROM performance_audits pa
      JOIN projects p ON p.id=pa.project_id
      WHERE p.user_id=u.id AND p.deleted_at IS NULL AND pa.strategy='MOBILE' AND pa.performance_score IS NOT NULL) AS average_performance_score,
    (SELECT COUNT(*) FROM reports r
      JOIN projects p ON p.id=r.project_id
      WHERE p.user_id=u.id AND p.deleted_at IS NULL AND r.deleted_at IS NULL) AS reports_generated,
    (SELECT COUNT(*) FROM optimization_suggestions o
      JOIN projects p ON p.id=o.project_id
      WHERE p.user_id=u.id AND p.deleted_at IS NULL AND o.priority IN ('CRITICAL','HIGH') AND o.status='OPEN') AS high_priority_issues
FROM users u
WHERE u.deleted_at IS NULL;

CREATE OR REPLACE VIEW vw_recommendation_cost_summary AS
SELECT
    r.id AS recommendation_id,
    r.project_id,
    r.analysis_run_id,
    r.recommended_option,
    r.estimated_min_monthly_cost_usd,
    r.estimated_max_monthly_cost_usd,
    pi.current_monthly_hosting_cost_usd,
    CASE
        WHEN pi.current_monthly_hosting_cost_usd IS NULL
          OR r.estimated_min_monthly_cost_usd IS NULL
          OR r.estimated_max_monthly_cost_usd IS NULL
        THEN NULL
        ELSE pi.current_monthly_hosting_cost_usd - ((r.estimated_min_monthly_cost_usd + r.estimated_max_monthly_cost_usd) / 2)
    END AS potential_saving_usd
FROM recommendations r
JOIN project_inputs pi ON pi.project_id = r.project_id;

-- Compatibility view for the naming used in the extended database prompt.
CREATE OR REPLACE VIEW vw_ml_training_jobs AS
SELECT
    id,
    public_id,
    user_id AS requested_by_user_id,
    model_type,
    status,
    current_stage,
    progress AS progress_percent,
    dataset_filename,
    dataset_row_count,
    started_at,
    completed_at,
    error_code,
    error_message AS error_message_safe,
    result_model_id AS created_model_version_id,
    created_at
FROM model_training_jobs;

-- ============================================================================
-- 16. SYSTEM SETTINGS SEED - NON-SECRET / VERSIONED
-- ============================================================================

INSERT INTO system_settings (id, setting_key, setting_value, data_type, description, is_public, config_version)
VALUES
('90000000-0000-0000-0000-000000000001','MAX_LOAD_TEST_VUS','500','INTEGER','Maximum virtual users allowed by prototype safety policy.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000002','MAX_LOAD_TEST_DURATION_SECONDS','1800','INTEGER','Maximum generated load-test duration in seconds.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000003','RECOMMENDATION_ML_WEIGHT','0.35','DECIMAL','ML fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000004','RECOMMENDATION_TRAFFIC_WEIGHT','0.20','DECIMAL','Traffic fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000005','RECOMMENDATION_BUDGET_WEIGHT','0.15','DECIMAL','Budget fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000006','RECOMMENDATION_SCALABILITY_WEIGHT','0.10','DECIMAL','Scalability fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000007','RECOMMENDATION_RELIABILITY_WEIGHT','0.10','DECIMAL','Reliability fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000008','RECOMMENDATION_OPERATIONAL_WEIGHT','0.10','DECIMAL','Operational fit weight in final recommendation scoring.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000009','CONFIDENCE_HIGH_THRESHOLD','0.80','DECIMAL','Confidence threshold for HIGH.',1,'1.0.0'),
('90000000-0000-0000-0000-000000000010','CONFIDENCE_MEDIUM_THRESHOLD','0.60','DECIMAL','Confidence threshold for MEDIUM.',1,'1.0.0'),
('90000000-0000-0000-0000-000000000011','CONFIDENCE_LOW_THRESHOLD','0.40','DECIMAL','Confidence threshold for LOW.',1,'1.0.0'),
('90000000-0000-0000-0000-000000000012','PRICING_STALE_DAYS','30','INTEGER','Stored pricing older than this may reduce confidence.',0,'1.0.0'),
('90000000-0000-0000-0000-000000000013','SUPPORTED_CURRENCY','USD','STRING','Only supported monetary currency for the entire project.',1,'1.0.0')
AS new
ON DUPLICATE KEY UPDATE
    setting_value = new.setting_value,
    data_type = new.data_type,
    description = new.description,
    is_public = new.is_public,
    config_version = new.config_version;

-- ============================================================================
-- 17. CLOUD PROVIDER + DEMO PRICING SEED
-- Pricing below is explicitly illustrative demo data, not claimed as live price.
-- ============================================================================

INSERT INTO cloud_providers (id, name, slug, provider_code, active)
VALUES
('91000000-0000-0000-0000-000000000001','DigitalOcean','digitalocean','DIGITALOCEAN',1),
('91000000-0000-0000-0000-000000000002','Hetzner','hetzner','HETZNER',1),
('91000000-0000-0000-0000-000000000003','AWS','aws','AWS',1),
('91000000-0000-0000-0000-000000000004','Google Cloud','google-cloud','GOOGLE_CLOUD',1),
('91000000-0000-0000-0000-000000000005','Azure','azure','AZURE',1),
('91000000-0000-0000-0000-000000000006','Vultr','vultr','VULTR',1)
AS new
ON DUPLICATE KEY UPDATE name = new.name, slug = new.slug, active = new.active;

INSERT INTO hosting_plans
(id, provider_id, plan_code, plan_name, architecture_type, region, region_code, region_name,
 vcpu, ram_gb, storage_gb, bandwidth_gb, managed, high_availability_supported,
 autoscaling_supported, base_monthly_cost, currency, source, active, is_demo)
VALUES
('92000000-0000-0000-0000-000000000001','91000000-0000-0000-0000-000000000001','DEMO-DO-VPS-2X4','Demo Basic 2x4','VPS','Singapore','sgp1','Singapore',2,4,80,2000,0,0,0,24.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000002','91000000-0000-0000-0000-000000000002','DEMO-HETZ-VPS-2X4','Demo CPX 2x4','VPS','Singapore','sg','Singapore',2,4,80,1000,0,0,0,18.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000003','91000000-0000-0000-0000-000000000001','DEMO-DO-VM-4X8','Demo General 4x8','CLOUD_VM','Singapore','sgp1','Singapore',4,8,160,4000,0,1,0,55.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000004','91000000-0000-0000-0000-000000000003','DEMO-AWS-VM-4X8','Demo General VM 4x8','CLOUD_VM','Singapore','ap-southeast-1','Singapore',4,8,100,NULL,0,1,0,70.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000005','91000000-0000-0000-0000-000000000004','DEMO-GCP-VM-4X8','Demo General VM 4x8','CLOUD_VM','Singapore','asia-southeast1','Singapore',4,8,100,NULL,0,1,0,75.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000006','91000000-0000-0000-0000-000000000005','DEMO-AZ-VM-4X8','Demo General VM 4x8','CLOUD_VM','Singapore','southeastasia','Singapore',4,8,100,NULL,0,1,0,80.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000007','91000000-0000-0000-0000-000000000001','DEMO-DO-K8S','Demo Managed K8s Baseline','KUBERNETES','Singapore','sgp1','Singapore',4,8,100,2000,1,1,1,120.00,'USD','DEMO_SEED_NOT_LIVE',1,1),
('92000000-0000-0000-0000-000000000008','91000000-0000-0000-0000-000000000003','DEMO-AWS-K8S','Demo Managed K8s Baseline','KUBERNETES','Singapore','ap-southeast-1','Singapore',4,8,100,NULL,1,1,1,150.00,'USD','DEMO_SEED_NOT_LIVE',1,1)
AS new
ON DUPLICATE KEY UPDATE
    plan_name=new.plan_name, vcpu=new.vcpu, ram_gb=new.ram_gb, storage_gb=new.storage_gb,
    bandwidth_gb=new.bandwidth_gb, base_monthly_cost=new.base_monthly_cost, currency='USD',
    source='DEMO_SEED_NOT_LIVE', active=1, is_demo=1;

INSERT INTO pricing_snapshots
(id, hosting_plan_id, min_monthly_cost, max_monthly_cost, currency, components, source, source_reference, effective_date, captured_at, is_current)
VALUES
('93000000-0000-0000-0000-000000000001','92000000-0000-0000-0000-000000000001',24.00,28.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000002','92000000-0000-0000-0000-000000000002',18.00,24.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000003','92000000-0000-0000-0000-000000000003',55.00,75.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000004','92000000-0000-0000-0000-000000000004',70.00,110.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000005','92000000-0000-0000-0000-000000000005',75.00,120.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000006','92000000-0000-0000-0000-000000000006',80.00,125.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000007','92000000-0000-0000-0000-000000000007',120.00,180.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1),
('93000000-0000-0000-0000-000000000008','92000000-0000-0000-0000-000000000008',150.00,240.00,'USD',JSON_OBJECT('note','Illustrative stored demo range only; replace with verified provider pricing.'),'DEMO_SEED_NOT_LIVE',NULL,CURRENT_DATE,CURRENT_TIMESTAMP(6),1)
AS new
ON DUPLICATE KEY UPDATE
    min_monthly_cost=new.min_monthly_cost, max_monthly_cost=new.max_monthly_cost,
    currency='USD', components=new.components, source=new.source, captured_at=new.captured_at, is_current=1;

-- ============================================================================
-- 18. OPTIONAL DEVELOPMENT USER SEED
-- This local-only sample account owns the coherent demonstration project below.
-- ============================================================================

SET @seed_user_email = _utf8mb4'demo@hostingadvisor.local' COLLATE utf8mb4_unicode_ci;
SET @seed_user_password_hash = '$2b$12$c1dP.qRmUNTINNgl7s0UWOF.uLU2ccHngnB3u4z44v9ML9mp1dCfW';
SET @seed_user_id = '94000000-0000-0000-0000-000000000001';

INSERT INTO users
(id, full_name, email, password_hash, role, status, is_verified, experience_level, default_region, timezone)
SELECT @seed_user_id, 'Hosting Advisor Demo User', @seed_user_email, @seed_user_password_hash,
       'USER', 'ACTIVE', 1, 'INTERMEDIATE', 'Sri Lanka', 'Asia/Colombo'
WHERE @seed_user_password_hash IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE email = @seed_user_email);

INSERT INTO user_preferences
(id, user_id, theme, default_currency, default_region, timezone, chart_animations, email_notifications, analysis_notifications)
SELECT '94000000-0000-0000-0000-000000000002', u.id, 'SYSTEM', 'USD', 'Sri Lanka', 'Asia/Colombo', 1, 1, 1
FROM users u
WHERE u.email = @seed_user_email
  AND NOT EXISTS (SELECT 1 FROM user_preferences up WHERE up.user_id = u.id);

-- ============================================================================
-- 19. COHERENT DEMO PROJECT LIFECYCLE (only inserted when sample user exists)
-- ============================================================================

INSERT INTO projects
(id, user_id, title, slug, mode, status, website_category, currency, target_region, description, is_demo)
SELECT
'95000000-0000-0000-0000-000000000001', u.id, 'Demo Planned E-commerce', 'demo-planned-ecommerce',
'PLANNED', 'COMPLETED', 'ECOMMERCE', 'USD', 'Singapore',
'Coherent demonstration project for dashboard, workload, recommendation, cost, optimization and reporting.', 1
FROM users u
WHERE u.email = @seed_user_email
  AND NOT EXISTS (SELECT 1 FROM projects WHERE id='95000000-0000-0000-0000-000000000001');

INSERT INTO project_inputs
(id, project_id, payload, completeness_score, target_region, frontend_framework, backend_framework, database_type,
 expected_monthly_users, peak_concurrent_users, requests_per_user_per_minute, traffic_growth, database_intensity,
 estimated_storage_gb, monthly_budget_usd, operational_skill, managed_database_preferred)
SELECT
'95000000-0000-0000-0000-000000000002', p.id,
JSON_OBJECT('projectName','Demo Planned E-commerce','frontend','Next.js','backend','FastAPI','database','MySQL','monthlyUsers',30000,'concurrentUsers',250,'budget',100,'currency','USD','managedDatabase',true),
0.95, 'Singapore','Next.js','FastAPI','MySQL',30000,250,10.0,'MEDIUM','MEDIUM',100.00,100.00,'INTERMEDIATE',1
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
  AND NOT EXISTS (SELECT 1 FROM project_inputs WHERE project_id=p.id);

INSERT INTO analysis_runs
(id, project_id, run_number, status, started_at, completed_at, is_latest)
SELECT
'95000000-0000-0000-0000-000000000003', p.id, 1, 'COMPLETED',
DATE_SUB(CURRENT_TIMESTAMP(6), INTERVAL 5 MINUTE), CURRENT_TIMESTAMP(6), 1
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
  AND NOT EXISTS (SELECT 1 FROM analysis_runs WHERE id='95000000-0000-0000-0000-000000000003');

UPDATE projects
SET latest_analysis_run_id='95000000-0000-0000-0000-000000000003'
WHERE id='95000000-0000-0000-0000-000000000001';

INSERT INTO workload_estimates
(id, project_id, analysis_run_id, concurrent_users, requests_per_user_per_minute, estimated_requests_per_minute,
 estimated_rps, peak_rps, peak_multiplier, classification, database_intensity, storage_gb, bandwidth_gb,
 growth_level, assumptions, evidence_quality, confidence_score, confidence_label)
SELECT
'95000000-0000-0000-0000-000000000004', p.id, '95000000-0000-0000-0000-000000000003',
250,10.0,5000.0,83.3333,125.0000,1.5,'MEDIUM','MEDIUM',100.00,1000.00,'MEDIUM',
JSON_ARRAY('10 requests per user per minute','1.5x peak multiplier'),0.85,0.84,'HIGH'
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
  AND NOT EXISTS (SELECT 1 FROM workload_estimates WHERE id='95000000-0000-0000-0000-000000000004');

INSERT INTO model_predictions
(id,analysis_run_id,project_id,model_version_id,predicted_class,prediction_confidence,probabilities,features,input_feature_snapshot_json)
SELECT '95000000-0000-0000-0000-000000000028','95000000-0000-0000-0000-000000000003',p.id,NULL,'CLOUD_VM',0.87,
JSON_OBJECT('VPS',0.10,'CLOUD_VM',0.87,'KUBERNETES',0.03),
JSON_OBJECT('workload_class','MEDIUM','peak_rps',125,'budget_usd',100),
JSON_OBJECT('expected_concurrent_users',250,'estimated_rps',83.3333,'peak_rps',125,'budget',100)
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM model_predictions WHERE id='95000000-0000-0000-0000-000000000028');

INSERT INTO model_prediction_probabilities (id,model_prediction_id,hosting_type,probability)
SELECT '95000000-0000-0000-0000-000000000029','95000000-0000-0000-0000-000000000028','VPS',0.10
WHERE EXISTS (SELECT 1 FROM model_predictions WHERE id='95000000-0000-0000-0000-000000000028')
AND NOT EXISTS (SELECT 1 FROM model_prediction_probabilities WHERE id='95000000-0000-0000-0000-000000000029');
INSERT INTO model_prediction_probabilities (id,model_prediction_id,hosting_type,probability)
SELECT '95000000-0000-0000-0000-000000000030','95000000-0000-0000-0000-000000000028','CLOUD_VM',0.87
WHERE EXISTS (SELECT 1 FROM model_predictions WHERE id='95000000-0000-0000-0000-000000000028')
AND NOT EXISTS (SELECT 1 FROM model_prediction_probabilities WHERE id='95000000-0000-0000-0000-000000000030');
INSERT INTO model_prediction_probabilities (id,model_prediction_id,hosting_type,probability)
SELECT '95000000-0000-0000-0000-000000000031','95000000-0000-0000-0000-000000000028','KUBERNETES',0.03
WHERE EXISTS (SELECT 1 FROM model_predictions WHERE id='95000000-0000-0000-0000-000000000028')
AND NOT EXISTS (SELECT 1 FROM model_prediction_probabilities WHERE id='95000000-0000-0000-0000-000000000031');

INSERT INTO recommendation_rule_results
(id,analysis_run_id,project_id,rule_code,rule_name,hosting_type,effect_type,score_delta,triggered,reason)
SELECT '95000000-0000-0000-0000-000000000032','95000000-0000-0000-0000-000000000003',p.id,'R_K8S_COMPLEXITY','Kubernetes complexity for medium workload','KUBERNETES','PENALTY',-15,1,'Kubernetes adds unnecessary operational complexity for this planned medium workload.'
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM recommendation_rule_results WHERE id='95000000-0000-0000-0000-000000000032');

INSERT INTO recommendations
(id, project_id, analysis_run_id, model_prediction_id, recommended_option, overall_score, confidence_value, confidence_label,
 resource_size, estimated_cost, alternatives, reasons, assumptions, warnings, rule_results, model_version,
 model_probabilities, is_current, is_stale, recommendation_engine_version, scoring_config_version)
SELECT
'95000000-0000-0000-0000-000000000005', p.id, '95000000-0000-0000-0000-000000000003','95000000-0000-0000-0000-000000000028',
'CLOUD_VM',88.00,0.87,'HIGH',
JSON_OBJECT('vcpu',4,'ram_gb',8,'storage_gb',100,'transfer_tb',1),
JSON_OBJECT('currency','USD','min',55.00,'max',80.00,'pricing_updated_at',CURRENT_TIMESTAMP()),
JSON_ARRAY(JSON_OBJECT('option','VPS','score',71),JSON_OBJECT('option','KUBERNETES','score',62)),
JSON_ARRAY(JSON_OBJECT('label','Traffic fit','score',91,'note','Suitable for the expected peak workload.'),JSON_OBJECT('label','Budget fit','score',82,'note','Fits the USD 100 monthly budget.')),
JSON_ARRAY('Planned traffic is based on user estimates.'),JSON_ARRAY(),JSON_ARRAY(),NULL,
JSON_OBJECT('VPS',0.10,'CLOUD_VM',0.87,'KUBERNETES',0.03),1,0,'1.0.0','1.0.0'
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
  AND NOT EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005');

INSERT INTO recommendation_scores
(id,recommendation_id,`option`,score,ml_probability,budget_fit,traffic_fit,scalability_fit,reliability_fit,operational_fit,is_recommended,rule_adjustments)
SELECT '95000000-0000-0000-0000-000000000006','95000000-0000-0000-0000-000000000005','CLOUD_VM',88,0.87,82,91,86,88,85,1,JSON_ARRAY()
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM recommendation_scores WHERE id='95000000-0000-0000-0000-000000000006');

INSERT INTO recommended_resources
(id,recommendation_id,vcpu,ram_gb,storage_gb,bandwidth_gb,database_strategy,managed_database_recommended,cdn_recommended,backup_strategy,monitoring_recommended,autoscaling_strategy)
SELECT '95000000-0000-0000-0000-000000000007','95000000-0000-0000-0000-000000000005',4,8,100,1000,'Managed MySQL',1,1,'Daily backup',1,'Horizontal scaling when sustained utilization requires it'
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM recommended_resources WHERE recommendation_id='95000000-0000-0000-0000-000000000005');

INSERT INTO recommendation_confidence_factors
(id,recommendation_id,factor_code,factor_score,weight,weighted_score,reason)
SELECT '95000000-0000-0000-0000-000000000008','95000000-0000-0000-0000-000000000005','ML_CERTAINTY',0.87,0.35,0.3045,'High model certainty for Cloud VM.'
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM recommendation_confidence_factors WHERE id='95000000-0000-0000-0000-000000000008');

INSERT INTO cost_estimates
(id,recommendation_id,hosting_type,compute_min_usd,compute_max_usd,database_min_usd,database_max_usd,total_min_usd,total_max_usd,current_cost_usd)
SELECT '95000000-0000-0000-0000-000000000009','95000000-0000-0000-0000-000000000005','CLOUD_VM',35,50,20,30,55,80,NULL
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM cost_estimates WHERE id='95000000-0000-0000-0000-000000000009');

INSERT INTO optimization_suggestions
(id,project_id,analysis_run_id,priority,category,title,explanation,impact,difficulty,benefit,status,steps)
SELECT '95000000-0000-0000-0000-000000000010',p.id,'95000000-0000-0000-0000-000000000003','HIGH','CACHE_CDN','Use a CDN for static assets','A CDN can reduce latency and origin load for users outside the deployment region.','Lower latency','EASY','Better global delivery','OPEN',JSON_ARRAY('Configure CDN','Cache static assets','Measure cache hit ratio')
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM optimization_suggestions WHERE id='95000000-0000-0000-0000-000000000010');

INSERT INTO project_activity_history
(id,project_id,user_id,analysis_run_id,activity_type,title,description)
SELECT '95000000-0000-0000-0000-000000000011',p.id,p.user_id,'95000000-0000-0000-0000-000000000003','ANALYSIS_COMPLETED','Demo analysis completed','Coherent seeded lifecycle for dashboard and project history.'
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM project_activity_history WHERE id='95000000-0000-0000-0000-000000000011');

-- Additional coherent demo evidence for project detail tabs.
INSERT INTO analysis_jobs
(id,project_id,analysis_run_id,status,current_stage,progress,stages_json,completed_stage_count,total_stage_count,started_at,completed_at)
SELECT '95000000-0000-0000-0000-000000000012',p.id,'95000000-0000-0000-0000-000000000003','COMPLETED','REPORT_PREPARATION',100,
JSON_ARRAY(
 JSON_OBJECT('name','URL_VALIDATION','status','COMPLETED'),
 JSON_OBJECT('name','TECHNOLOGY_DETECTION','status','COMPLETED'),
 JSON_OBJECT('name','PERFORMANCE_AUDIT','status','COMPLETED'),
 JSON_OBJECT('name','WORKLOAD_CALCULATION','status','COMPLETED'),
 JSON_OBJECT('name','RULE_EVALUATION','status','COMPLETED'),
 JSON_OBJECT('name','ML_PREDICTION','status','COMPLETED'),
 JSON_OBJECT('name','PRICING_COMPARISON','status','COMPLETED'),
 JSON_OBJECT('name','FINAL_SCORING','status','COMPLETED'),
 JSON_OBJECT('name','CONFIDENCE_CALCULATION','status','COMPLETED'),
 JSON_OBJECT('name','OPTIMIZATION_GENERATION','status','COMPLETED'),
 JSON_OBJECT('name','REPORT_PREPARATION','status','COMPLETED')),
11,11,DATE_SUB(CURRENT_TIMESTAMP(6),INTERVAL 5 MINUTE),CURRENT_TIMESTAMP(6)
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM analysis_jobs WHERE id='95000000-0000-0000-0000-000000000012');

UPDATE analysis_runs
SET job_id='95000000-0000-0000-0000-000000000012'
WHERE id='95000000-0000-0000-0000-000000000003';

INSERT INTO technology_detections
(id,project_id,analysis_run_id,technology,technology_version,category,confidence,confidence_label,detection_status,is_user_confirmed,user_correction)
SELECT '95000000-0000-0000-0000-000000000013',p.id,'95000000-0000-0000-0000-000000000003','Next.js',NULL,'FRONTEND',0.98,'HIGH','DETECTED',1,NULL
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM technology_detections WHERE id='95000000-0000-0000-0000-000000000013');

INSERT INTO technology_evidence
(id,detection_id,source,pattern,value_masked,weight)
SELECT '95000000-0000-0000-0000-000000000014','95000000-0000-0000-0000-000000000013','USER_DECLARED','Declared in planned project input',NULL,0.98
WHERE EXISTS (SELECT 1 FROM technology_detections WHERE id='95000000-0000-0000-0000-000000000013')
AND NOT EXISTS (SELECT 1 FROM technology_evidence WHERE id='95000000-0000-0000-0000-000000000014');

INSERT INTO performance_audits
(id,project_id,analysis_run_id,strategy,status,performance_score,accessibility_score,best_practices_score,seo_score,metrics_json,source,warning,audited_at)
SELECT '95000000-0000-0000-0000-000000000015',p.id,'95000000-0000-0000-0000-000000000003','MOBILE','UNAVAILABLE',NULL,NULL,NULL,NULL,
JSON_OBJECT(),'NOT_LIVE','Performance audit is unavailable for a planned website.',CURRENT_TIMESTAMP(6)
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM performance_audits WHERE id='95000000-0000-0000-0000-000000000015');

INSERT INTO recommendation_reasons
(id,recommendation_id,hosting_type,reason_type,title,description,importance,display_order)
SELECT '95000000-0000-0000-0000-000000000016','95000000-0000-0000-0000-000000000005','CLOUD_VM','POSITIVE','Traffic fit','Expected peak workload fits a Cloud VM without Kubernetes complexity.','HIGH',1
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM recommendation_reasons WHERE id='95000000-0000-0000-0000-000000000016');

INSERT INTO recommendation_assumptions
(id,recommendation_id,assumption_key,assumption_value,description,confidence_impact)
SELECT '95000000-0000-0000-0000-000000000017','95000000-0000-0000-0000-000000000005','PLANNED_TRAFFIC','30000 monthly / 250 concurrent','Traffic values are user-provided planning estimates.',0.05
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM recommendation_assumptions WHERE id='95000000-0000-0000-0000-000000000017');

INSERT INTO architecture_nodes
(id,recommendation_id,node_key,node_type,label,description,position_x,position_y,display_order,metadata_json)
SELECT '95000000-0000-0000-0000-000000000018','95000000-0000-0000-0000-000000000005','users','CLIENT','Users','Application users',0,100,1,JSON_OBJECT()
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_nodes WHERE id='95000000-0000-0000-0000-000000000018');
INSERT INTO architecture_nodes
(id,recommendation_id,node_key,node_type,label,description,position_x,position_y,display_order,metadata_json)
SELECT '95000000-0000-0000-0000-000000000019','95000000-0000-0000-0000-000000000005','cdn','CDN','CDN','Static asset delivery',250,100,2,JSON_OBJECT()
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_nodes WHERE id='95000000-0000-0000-0000-000000000019');
INSERT INTO architecture_nodes
(id,recommendation_id,node_key,node_type,label,description,position_x,position_y,display_order,metadata_json)
SELECT '95000000-0000-0000-0000-000000000020','95000000-0000-0000-0000-000000000005','app','APPLICATION','Cloud VM','FastAPI application workload',500,100,3,JSON_OBJECT()
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_nodes WHERE id='95000000-0000-0000-0000-000000000020');
INSERT INTO architecture_nodes
(id,recommendation_id,node_key,node_type,label,description,position_x,position_y,display_order,metadata_json)
SELECT '95000000-0000-0000-0000-000000000021','95000000-0000-0000-0000-000000000005','db','DATABASE','Managed MySQL','Primary relational database',750,100,4,JSON_OBJECT()
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_nodes WHERE id='95000000-0000-0000-0000-000000000021');

INSERT INTO architecture_edges (id,recommendation_id,source_node_key,target_node_key,edge_label,display_order)
SELECT '95000000-0000-0000-0000-000000000022','95000000-0000-0000-0000-000000000005','users','cdn','HTTPS',1
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_edges WHERE id='95000000-0000-0000-0000-000000000022');
INSERT INTO architecture_edges (id,recommendation_id,source_node_key,target_node_key,edge_label,display_order)
SELECT '95000000-0000-0000-0000-000000000023','95000000-0000-0000-0000-000000000005','cdn','app','Origin',2
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_edges WHERE id='95000000-0000-0000-0000-000000000023');
INSERT INTO architecture_edges (id,recommendation_id,source_node_key,target_node_key,edge_label,display_order)
SELECT '95000000-0000-0000-0000-000000000024','95000000-0000-0000-0000-000000000005','app','db','SQL',3
WHERE EXISTS (SELECT 1 FROM recommendations WHERE id='95000000-0000-0000-0000-000000000005')
AND NOT EXISTS (SELECT 1 FROM architecture_edges WHERE id='95000000-0000-0000-0000-000000000024');

INSERT INTO reports
(id,project_id,user_id,analysis_run_id,recommendation_id,report_title,version,status,snapshot,file_key,generated_at)
SELECT '95000000-0000-0000-0000-000000000025',p.id,p.user_id,'95000000-0000-0000-0000-000000000003','95000000-0000-0000-0000-000000000005','Demo Planned E-commerce - Analysis Report',1,'READY',
JSON_OBJECT('project',JSON_OBJECT('id',p.id,'title',p.title,'mode',p.mode,'currency','USD'),'recommendation',JSON_OBJECT('recommended_option','CLOUD_VM','overall_score',88,'estimated_cost',JSON_OBJECT('currency','USD','min',55,'max',80))),'report-demo-planned-ecommerce-v1.pdf',CURRENT_TIMESTAMP(6)
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM reports WHERE id='95000000-0000-0000-0000-000000000025');

INSERT INTO report_versions
(id,report_id,version_number,executive_summary,report_snapshot_json,pdf_storage_key,model_version,pricing_snapshot_date,generated_at)
SELECT '95000000-0000-0000-0000-000000000026','95000000-0000-0000-0000-000000000025',1,'Cloud VM recommended for the planned e-commerce workload.',r.snapshot,r.file_key,NULL,CURRENT_TIMESTAMP(6),CURRENT_TIMESTAMP(6)
FROM reports r
WHERE r.id='95000000-0000-0000-0000-000000000025'
AND NOT EXISTS (SELECT 1 FROM report_versions WHERE id='95000000-0000-0000-0000-000000000026');

INSERT INTO notifications
(id,user_id,project_id,type,title,message,action_url,is_read,read_at,data)
SELECT '95000000-0000-0000-0000-000000000027',p.user_id,p.id,'ANALYSIS_COMPLETED','Analysis completed','Demo Planned E-commerce is ready to review.',CONCAT('/projects/',p.id),0,NULL,JSON_OBJECT('project_id',p.id,'analysis_run_id','95000000-0000-0000-0000-000000000003')
FROM projects p
WHERE p.id='95000000-0000-0000-0000-000000000001'
AND NOT EXISTS (SELECT 1 FROM notifications WHERE id='95000000-0000-0000-0000-000000000027');

SELECT 'ai_web_hosting_advisor schema installed successfully - USD only' AS installation_status;
