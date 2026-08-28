from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AI Web Hosting Advisor"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./hosting_advisor.db"
    jwt_secret: str = "development-only-change-this-secret-32chars"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    password_reset_minutes: int = 30
    frontend_url: str = "http://localhost:3000"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "AI Web Hosting Advisor"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    password_reset_return_token: bool = False
    cors_origins: list[str] | str = ["http://localhost:3000"]
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False
    pagespeed_api_key: str | None = None
    pagespeed_cache_seconds: int = 900
    llm_enabled: bool = False
    openrouter_api_key: str | None = None
    openrouter_model: str = "z-ai/glm-5.2:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 30.0
    openrouter_max_tokens: int = 1200
    openrouter_retry_attempts: int = 3
    openrouter_http_referer: str | None = None
    openrouter_app_title: str = "AI Web Hosting Advisor"
    classifier_model_path: str = "models/classifier/production/LogisticRegression_full5000.joblib"
    resource_model_path: str = "models/resource/production/RandomForestRegressor_full5000.joblib"
    seed_admin_email: str = "admin@hostingadvisor.local"
    seed_admin_password: str = "Admin123!ChangeMe"
    k6_max_vus: int = 500
    k6_max_duration_seconds: int = 1800
    k6_default_p95_threshold_ms: int = 2000
    k6_default_error_rate_threshold: float = 0.01
    k6_max_redirects: int = 5
    k6_allow_stress_test: bool = True
    k6_allow_spike_test: bool = True
    k6_allow_soak_test: bool = True
    k6_result_max_file_mb: int = 5
    k6_plan_generation_limit_per_hour: int = 20
    k6_result_import_limit_per_hour: int = 20
    k6_binary_path: str = "k6"
    k6_default_p99_threshold_ms: int = 4000
    k6_default_check_pass_rate: float = 0.99
    managed_load_test_max_concurrency: int = 10
    managed_load_test_max_duration_seconds: int = 120
    managed_load_test_run_limit_per_hour: int = 10
    managed_load_test_execution_timeout_seconds: int = 120
    max_external_response_bytes: int = 2_000_000
    max_redirects: int = 3
    http_connect_timeout: float = 5.0
    http_read_timeout: float = 12.0
    report_storage_dir: str = "storage/reports"
    load_test_storage_dir: str = "storage/load_tests"
    log_level: str = "INFO"
    pricing_stale_days: int = 30
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    auto_create_tables: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    def ensure_storage(self):
        Path(self.report_storage_dir).mkdir(parents=True, exist_ok=True)
        Path(self.load_test_storage_dir).mkdir(parents=True, exist_ok=True)

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_storage()
    return s

settings = get_settings()
