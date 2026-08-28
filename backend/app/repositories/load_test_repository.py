from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import LoadTestPlan,LoadTestStage,LoadTestResult

def get_plan(db:Session,plan_id:str,user_id:str)->LoadTestPlan|None:
    return db.scalar(select(LoadTestPlan).where((LoadTestPlan.id==plan_id)|(LoadTestPlan.public_id==plan_id),LoadTestPlan.user_id==user_id))

def list_project_plans(db:Session,project_id:str,user_id:str)->list[LoadTestPlan]:
    return list(db.scalars(select(LoadTestPlan).where(LoadTestPlan.project_id==project_id,LoadTestPlan.user_id==user_id).order_by(LoadTestPlan.created_at.desc())))

def list_stages(db:Session,plan_id:str)->list[LoadTestStage]:
    return list(db.scalars(select(LoadTestStage).where(LoadTestStage.load_test_plan_id==plan_id).order_by(LoadTestStage.stage_order)))

def list_results(db:Session,plan_id:str)->list[LoadTestResult]:
    return list(db.scalars(select(LoadTestResult).where(LoadTestResult.load_test_plan_id==plan_id).order_by(LoadTestResult.created_at.desc())))
