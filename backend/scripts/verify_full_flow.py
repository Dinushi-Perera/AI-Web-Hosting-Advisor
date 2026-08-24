"""Run a disposable SQLite end-to-end verification of the application APIs."""

import os
import sys
import tempfile
import warnings
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

run_dir = Path(tempfile.mkdtemp(prefix="hosting-advisor-flow-"))
report_dir = run_dir / "pdfs"
os.environ["DATABASE_URL"] = f"sqlite:///{(run_dir / 'flow.db').as_posix()}"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["REPORT_STORAGE_DIR"] = str(report_dir)
os.environ["JWT_SECRET"] = "full-flow-verification-secret-that-is-long-enough"
os.environ["PASSWORD_RESET_RETURN_TOKEN"] = "true"
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_FROM_EMAIL"] = ""
warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated")

from fastapi.testclient import TestClient
from sqlalchemy import select
from app.core.database import Base, engine, SessionLocal
from app.core.security import verify_password
from app.main import app
from app.models import AuditLog, PasswordResetToken, User, UserPreference, UserSession, Recommendation, ModelPrediction

Base.metadata.create_all(bind=engine)
client = TestClient(app)

registration = client.post("/api/v1/auth/register", json={
    "fullName": "Database Flow User",
    "email": "flow@example.com",
    "password": "Verified123!",
})
assert registration.status_code == 201, registration.text
assert client.get("/api/v1/auth/me").status_code == 200

profile = client.patch("/api/v1/users/me", json={
    "fullName": "Updated Database Flow User",
    "email": "flow@example.com",
    "experienceLevel": "Intermediate",
    "defaultRegion": "Sri Lanka",
    "timezone": "Asia/Colombo",
    "currency": "USD",
})
profile.raise_for_status()
assert profile.json()["fullName"] == "Updated Database Flow User"

preferences = client.patch("/api/v1/users/me/preferences", json={
    "theme": "dark",
    "defaultCurrency": "USD",
    "defaultRegion": "Sri Lanka",
    "timezone": "Asia/Colombo",
    "chartAnimations": True,
    "emailNotifications": True,
    "analysisNotifications": True,
    "onboardingCompleted": True,
})
preferences.raise_for_status()
assert preferences.json()["onboardingCompleted"] is True

logout = client.post("/api/v1/auth/logout")
logout.raise_for_status()
assert client.get("/api/v1/auth/me").status_code == 401
login = client.post("/api/v1/auth/login", json={"email":"flow@example.com","password":"Verified123!","remember":True})
login.raise_for_status()
assert client.get("/api/v1/dashboard").status_code == 200

analysis = client.post("/api/v1/analysis/planned", json={
    "projectName": "Verified Planned Project",
    "websiteType": "SaaS",
    "region": "Singapore",
    "monthlyUsers": "50000",
    "concurrentUsers": "250",
    "budget": "100",
    "currency": "USD",
})
analysis.raise_for_status()
project_id = analysis.json()["projectId"]
job_id = analysis.json()["jobId"]
status = client.get(f"/api/v1/analysis/jobs/{job_id}")
status.raise_for_status()
assert status.json()["status"] == "COMPLETED", status.json()

projects = client.get("/api/v1/projects")
projects.raise_for_status()
assert any(item["id"] == project_id for item in projects.json())

report = client.post(f"/api/v1/projects/{project_id}/reports")
report.raise_for_status()
report_id = report.json()["id"]
pdf_response = client.get(f"/api/v1/reports/{report_id}/pdf")
pdf_response.raise_for_status()
assert pdf_response.headers["content-type"].startswith("application/pdf")
assert pdf_response.content.startswith(b"%PDF")

forgot = client.post("/api/v1/auth/forgot-password", json={"email":"flow@example.com"})
forgot.raise_for_status()
reset_token = forgot.json().get("developmentResetToken")
assert reset_token
reset = client.post("/api/v1/auth/reset-password", json={"token":reset_token,"password":"Changed123!"})
reset.raise_for_status()

fresh = TestClient(app)
assert fresh.post("/api/v1/auth/login", json={"email":"flow@example.com","password":"Verified123!","remember":True}).status_code == 401
new_login = fresh.post("/api/v1/auth/login", json={"email":"flow@example.com","password":"Changed123!","remember":True})
new_login.raise_for_status()
assert fresh.get("/api/v1/dashboard").status_code == 200
unknown = fresh.post("/api/v1/auth/forgot-password", json={"email":"nobody@example.com"})
unknown.raise_for_status()
assert "developmentResetToken" not in unknown.json()

db = SessionLocal()
try:
    stored_user = db.scalar(select(User).where(User.email == "flow@example.com"))
    assert stored_user is not None
    assert stored_user.full_name == "Updated Database Flow User"
    assert stored_user.password_hash not in {"Verified123!", "Changed123!"}
    assert stored_user.password_hash.startswith("$2")
    assert verify_password("Changed123!", stored_user.password_hash)
    assert not verify_password("Verified123!", stored_user.password_hash)
    assert stored_user.last_login_at is not None
    assert stored_user.failed_login_count == 0

    stored_preferences = db.scalar(select(UserPreference).where(UserPreference.user_id == stored_user.id))
    assert stored_preferences is not None
    assert stored_preferences.theme == "DARK"
    assert stored_preferences.onboarding_completed is True

    stored_sessions = list(db.scalars(select(UserSession).where(UserSession.user_id == stored_user.id)))
    assert len(stored_sessions) >= 3
    assert any(session.revoked_at is not None for session in stored_sessions)
    assert any(session.revoked_at is None for session in stored_sessions)

    stored_resets = list(db.scalars(select(PasswordResetToken).where(PasswordResetToken.user_id == stored_user.id)))
    assert len(stored_resets) == 1
    assert stored_resets[0].used_at is not None
    assert stored_resets[0].nonce_hash != reset_token

    audit_actions = set(db.scalars(select(AuditLog.action).where(AuditLog.actor_user_id == stored_user.id)))
    assert {"REGISTER", "LOGIN", "PROFILE_UPDATE", "PREFERENCES_UPDATE", "PASSWORD_RESET_REQUEST", "PASSWORD_RESET"}.issubset(audit_actions)

    recommendation = db.scalar(select(Recommendation).where(Recommendation.project_id == project_id))
    prediction = db.scalar(select(ModelPrediction).where(ModelPrediction.analysis_run_id == recommendation.analysis_run_id))
    assert recommendation.model_version == "hosting-classifier-selected-full5000"
    assert recommendation.resource_size["model_source"] == "TRAINED_MODEL"
    assert recommendation.resource_size["model_version"] == "resource-sizer-selected-full5000"
    assert set(prediction.features) == set(__import__("app.services.ml_service", fromlist=["MODEL_FEATURES"]).MODEL_FEATURES)
finally:
    db.close()

pdf_files = list(report_dir.glob("*.pdf"))
assert len(pdf_files) == 1, pdf_files
print(f"FLOW_OK user={registration.json()['user']['id']} project={project_id} report={report_id}")
print(f"AUTH_DB_OK sessions={len(stored_sessions)} reset_tokens={len(stored_resets)} audits={len(audit_actions)}")
print(f"PDF_PATH={pdf_files[0].resolve()}")
sys.exit(0)
