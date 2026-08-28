"""Run a disposable SQLite end-to-end verification of the application APIs."""

import os
import sys
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

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
from app.models import AuditLog, PasswordResetToken, User, UserPreference, UserSession, Recommendation, ModelPrediction, ProjectClarification, Optimization
from scripts.seed import main as seed_database

Base.metadata.create_all(bind=engine)
seed_database()
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
    "timezone": "Asia/Colombo",
})
profile.raise_for_status()
assert profile.json()["fullName"] == "Updated Database Flow User"

preferences = client.patch("/api/v1/users/me/preferences", json={
    "theme": "dark",
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
    "monthlyUsers": "50000",
    "concurrentUsers": "250",
    "budget": "100",
})
analysis.raise_for_status()
project_id = analysis.json()["projectId"]
job_id = analysis.json()["jobId"]
status = client.get(f"/api/v1/analysis/jobs/{job_id}")
status.raise_for_status()
assert status.json()["status"] == "COMPLETED", status.json()

clarification_preview=client.post("/api/v1/analysis/clarification-questions",json={"idea":"A scheduling and payments platform for independent service businesses","industry":"SaaS","targetUsers":"Independent businesses","features":["Login","Payments","Bookings"],"traffic":"Growing business","budget":120,"timeline":"3-6 months","experience":"Intermediate"})
clarification_preview.raise_for_status()
assert {item["key"] for item in clarification_preview.json()["questions"]} == {"concurrentUsers","storage","dbWorkload"}
idea=client.post("/api/v1/analysis/idea",json={"idea":"A scheduling and payments platform for independent service businesses","industry":"SaaS","targetUsers":"Independent businesses","features":["Login","Payments","Bookings"],"traffic":"Growing business","budget":120,"timeline":"3-6 months","experience":"Intermediate","clarifications":{"concurrentUsers":"180","storage":"120","dbWorkload":"High"}})
idea.raise_for_status();idea_project_id=idea.json()["projectId"]
idea_status=client.get(f"/api/v1/analysis/jobs/{idea.json()['jobId']}");idea_status.raise_for_status()
assert idea_status.json()["status"] == "COMPLETED",idea_status.json()
idea_workload=client.get(f"/api/v1/projects/{idea_project_id}/workload");idea_workload.raise_for_status()
assert idea_workload.json()["concurrent_users"] == 180
assert idea_workload.json()["storage_gb"] == 120
assert idea_workload.json()["database_intensity"] == "HIGH"

fake_response={"url":"https://example.com/","status_code":200,"response_time_ms":80,"headers":{"server":"nginx","strict-transport-security":"max-age=31536000"},"content":b'<html><script id="__NEXT_DATA__"></script><script src="/_next/static/app.js"></script></html>'}
fake_performance=[{"strategy":strategy,"status":"AVAILABLE","performance_score":82 if strategy=="MOBILE" else 91,"accessibility_score":96,"best_practices_score":94,"seo_score":93,"metrics":{"lcp_ms":2200,"inp_ms":160,"cls":.05,"fcp_ms":1400,"tbt_ms":130,"speed_index_ms":2800},"statuses":{},"warning":None} for strategy in ("MOBILE","DESKTOP")]
with patch("app.services.analysis_pipeline.validate_public_url",return_value="https://example.com/"),patch("app.services.analysis_pipeline.safe_fetch",return_value=fake_response),patch("app.services.analysis_pipeline.performance_audit",return_value=fake_performance):
    live=client.post("/api/v1/analysis/live",json={"projectName":"Verified Live Website","websiteUrl":"https://example.com/","category":"SaaS","monthlyVisitors":40000,"concurrentUsers":160,"growth":"Medium Growth","trafficPattern":"Business Hours","budget":140,"budgetFlexibility":"Some flexibility","managesServers":True,"highAvailability":True,"rapidScaling":False,"kubernetesSkill":False,"managedDatabase":True,"backups":True})
live.raise_for_status();live_project_id=live.json()["projectId"]
live_status=client.get(f"/api/v1/analysis/jobs/{live.json()['jobId']}");live_status.raise_for_status()
assert live_status.json()["status"] == "COMPLETED",live_status.json()

section_paths=("analysis-summary","technology","performance","performance/history","workload","recommendation","recommendation/explanation","recommendation/compare","architecture","cost","optimizations","history","reports","load-test/recommendation","load-tests/history")
for verified_project_id in (project_id,idea_project_id,live_project_id):
    overview=client.get(f"/api/v1/projects/{verified_project_id}");overview.raise_for_status()
    assert overview.json()["status"] == "Completed"
    for section_path in section_paths:
        response=client.get(f"/api/v1/projects/{verified_project_id}/{section_path}")
        response.raise_for_status()
    summary=client.get(f"/api/v1/projects/{verified_project_id}/analysis-summary").json()
    assert len(summary["coverage"]) == 8
    assert len(summary["decisionFactors"]) == 5
    assert set(summary["testing"]) == {"UT","IT","ST","UAT","ORT"}
    assert len(summary["projectTests"]) == 9
    assert all(case["status"] == "PASSED" for case in summary["projectTests"]),summary["projectTests"]
    generated_reports=client.get(f"/api/v1/projects/{verified_project_id}/reports");generated_reports.raise_for_status()
    report_snapshot=client.get(f"/api/v1/reports/{generated_reports.json()[0]['id']}");report_snapshot.raise_for_status()
    report_project_tests=[row for row in report_snapshot.json()["snapshot"]["testing"]["results"] if (row.get("details") or {}).get("project_id")==verified_project_id]
    assert len(report_project_tests)==9
    recommendation_data=client.get(f"/api/v1/projects/{verified_project_id}/recommendation").json()
    assert [item["rank"] for item in recommendation_data["alternatives"]] == [1,2,3]
    assert all("score_breakdown" in item for item in recommendation_data["alternatives"])
    cost_data=client.get(f"/api/v1/projects/{verified_project_id}/cost").json()
    assert len(cost_data["ranked_options"]) == 3
    assert cost_data["annual_range"]["min"] == cost_data["recommended_range"]["min"]*12

providers=client.get("/api/v1/pricing/providers");providers.raise_for_status()

projects = client.get("/api/v1/projects")
projects.raise_for_status()
assert {project_id,idea_project_id,live_project_id}.issubset({item["id"] for item in projects.json()})

report = client.post(f"/api/v1/projects/{project_id}/reports")
report.raise_for_status()
report_id = report.json()["id"]
pdf_response = client.get(f"/api/v1/reports/{report_id}/pdf")
pdf_response.raise_for_status()
assert pdf_response.headers["content-type"].startswith("application/pdf")
assert pdf_response.content.startswith(b"%PDF")

optimization_rows=client.get(f"/api/v1/projects/{project_id}/optimizations");optimization_rows.raise_for_status()
assert optimization_rows.json()
optimization_update=client.patch(f"/api/v1/optimizations/{optimization_rows.json()[0]['id']}/status",json={"status":"DONE"});optimization_update.raise_for_status()
feedback_response=client.post(f"/api/v1/projects/{project_id}/feedback",json={"clarity_rating":5,"usefulness_rating":5,"ease_of_use_rating":5,"recommendation_trust_rating":5,"comments":"Verified full-flow feedback"});feedback_response.raise_for_status()
history_response=client.get(f"/api/v1/projects/{project_id}/history");history_response.raise_for_status()
history_actions={event["action"] for event in history_response.json()["events"]}
assert {"REPORT_GENERATED","OPTIMIZATION_STATUS_UPDATED","UAT_FEEDBACK_SUBMITTED"}.issubset(history_actions)
notifications_response=client.get("/api/v1/notifications");notifications_response.raise_for_status()
notification_types={item["type"] for item in notifications_response.json() if (item.get("data") or {}).get("project_id")==project_id}
assert {"ANALYSIS_COMPLETED","REPORT_READY","OPTIMIZATION_UPDATED","FEEDBACK_SAVED"}.issubset(notification_types)

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
    stored_clarifications=list(db.scalars(select(ProjectClarification).where(ProjectClarification.project_id==idea_project_id)))
    assert {row.question_key:row.answer_value for row in stored_clarifications} == {"concurrentUsers":"180","storage":"120","dbWorkload":"High"}
    optimization_categories=set(db.scalars(select(Optimization.category).where(Optimization.project_id.in_([project_id,idea_project_id,live_project_id]))))
    assert {"COST","MONITORING"}.issubset(optimization_categories)
finally:
    db.close()

pdf_files = list(report_dir.glob("*.pdf"))
assert len(pdf_files) >= 4, pdf_files
assert len([path for path in pdf_files if report_id in path.name]) == 1
print(f"FLOW_OK user={registration.json()['user']['id']} project={project_id} report={report_id}")
print(f"MODES_OK planned={project_id} idea={idea_project_id} live={live_project_id} sections={len(section_paths)}")
print(f"AUTH_DB_OK sessions={len(stored_sessions)} reset_tokens={len(stored_resets)} audits={len(audit_actions)}")
print(f"PDF_COUNT={len(pdf_files)}")
sys.exit(0)
