"""Idempotently add input-specific validation evidence to completed projects."""

import sys
from pathlib import Path

from sqlalchemy import select

backend_root=Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0,str(backend_root))

from app.core.database import SessionLocal
from app.models import Project
from app.services.project_validation_service import evaluate_project


def main():
    db=SessionLocal()
    updated=0
    try:
        projects=list(db.scalars(select(Project).where(Project.latest_analysis_run_id.is_not(None),Project.deleted_at.is_(None))))
        for project in projects:
            cases=evaluate_project(db,project,project.latest_analysis_run_id,persist=True)
            if cases:
                updated+=1
        print(f"Project validation evidence checked for {updated} completed projects.")
    finally:
        db.close()


if __name__=="__main__":
    main()
