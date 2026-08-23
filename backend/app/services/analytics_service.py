from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Project, PerformanceAudit, Recommendation, Report, Optimization, AnalysisRun
from app.services.project_service import ProjectService

def dashboard(db:Session,user):
    projects=list(db.scalars(select(Project).where(Project.user_id==user.id,Project.deleted_at.is_(None))))
    pids=[p.id for p in projects]
    completed=sum(1 for p in projects if p.status=="COMPLETED")
    perf=[]; recs=[]; reports=[]; high=0
    if pids:
        perf=list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.project_id.in_(pids),PerformanceAudit.strategy=="MOBILE",PerformanceAudit.performance_score.is_not(None))))
        recs=list(db.scalars(select(Recommendation).where(Recommendation.project_id.in_(pids))))
        reports=list(db.scalars(select(Report).where(Report.project_id.in_(pids),Report.deleted_at.is_(None))))
        high=db.scalar(select(func.count(Optimization.id)).where(Optimization.project_id.in_(pids),Optimization.priority.in_(["HIGH","CRITICAL"]),Optimization.status=="OPEN")) or 0
    avg=round(sum(x.performance_score for x in perf)/len(perf)) if perf else None
    dist={"VPS":0,"CLOUD_VM":0,"KUBERNETES":0}
    for r in recs: dist[r.recommended_option]=dist.get(r.recommended_option,0)+1
    recent=sorted(projects,key=lambda p:p.updated_at,reverse=True)[:5]
    return {"summary":{"total_projects":len(projects),"completed_analyses":completed,"average_performance_score":avg,"estimated_monthly_savings":None,"reports_generated":len(reports),"high_priority_issues":high,"currency":"USD"},"recent_projects":[ProjectService(db).serialize(p) for p in recent],"performance_trend":[{"date":x.audited_at.isoformat(),"performance":x.performance_score,"project_id":x.project_id} for x in sorted(perf,key=lambda x:x.audited_at)[-30:]],"hosting_distribution":dist,"cost_summary":{"currency":"USD","note":"Savings are not fabricated; current-vs-recommended cost is required before a savings figure is returned."},"priority_issues":high,"recent_activity":[]}
