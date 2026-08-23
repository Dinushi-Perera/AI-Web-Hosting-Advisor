from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from app.models import Project, ProjectInput, TechnologyDetection, TechnologyEvidence, PerformanceAudit, WorkloadEstimate, Recommendation, Optimization, Report, AnalysisRun
from app.core.config import settings
from app.core.exceptions import AppError

def _iso(v): return v.isoformat() if hasattr(v,"isoformat") else v

def snapshot(db:Session,project:Project,run_id:str):
    inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project.id))
    tech=[]
    for t in db.scalars(select(TechnologyDetection).where(TechnologyDetection.analysis_run_id==run_id)):
        ev=list(db.scalars(select(TechnologyEvidence).where(TechnologyEvidence.detection_id==t.id)))
        tech.append({"technology":t.technology,"category":t.category,"confidence":t.confidence,"confidence_label":t.confidence_label,"evidence":[{"source":e.source,"pattern":e.pattern,"weight":e.weight} for e in ev]})
    perf=[{"strategy":a.strategy,"status":a.status,"performance_score":a.performance_score,"accessibility_score":a.accessibility_score,"best_practices_score":a.best_practices_score,"seo_score":a.seo_score,"metrics":a.metrics_json,"warning":a.warning,"audited_at":_iso(a.audited_at)} for a in db.scalars(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==run_id))]
    w=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==run_id)); r=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==run_id)); opts=list(db.scalars(select(Optimization).where(Optimization.analysis_run_id==run_id)))
    if not r: raise AppError("REPORT_GENERATION_FAILED","A completed recommendation is required before generating a report.",409)
    return {"project":{"id":project.id,"title":project.title,"mode":project.mode,"website_url":project.website_url,"currency":"USD","target_region":project.target_region},"input":inp.payload if inp else {},"technology":tech,"performance":perf,"workload":{"concurrent_users":w.concurrent_users,"estimated_rps":w.estimated_rps,"peak_rps":w.peak_rps,"classification":w.classification,"database_intensity":w.database_intensity,"storage_gb":w.storage_gb,"bandwidth_gb":w.bandwidth_gb,"growth_level":w.growth_level,"assumptions":w.assumptions} if w else {},"recommendation":{"recommended_option":r.recommended_option,"overall_score":r.overall_score,"confidence":{"value":r.confidence_value,"label":r.confidence_label},"resource_size":r.resource_size,"estimated_cost":r.estimated_cost,"alternatives":r.alternatives,"reasons":r.reasons,"assumptions":r.assumptions,"warnings":r.warnings,"model_version":r.model_version},"optimizations":[{"priority":o.priority,"category":o.category,"title":o.title,"explanation":o.explanation,"difficulty":o.difficulty,"status":o.status,"steps":o.steps} for o in opts],"snapshot_generated_at":datetime.now(timezone.utc).isoformat()}

def _money(cost):
    if not cost or cost.get("min") is None:return "Unavailable"
    return f"USD {cost.get('min'):.2f} - {cost.get('max'):.2f} / month"

def render_pdf(snap:dict,path:Path):
    styles=getSampleStyleSheet(); doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm,title=f"AI Hosting Advisor - {snap['project']['title']}")
    story=[Paragraph("AI-Driven Web Hosting Advisor Report",styles["Title"]),Spacer(1,8),Paragraph(snap["project"]["title"],styles["Heading2"]),Paragraph(f"All cost figures in this report use USD. Generated {snap['snapshot_generated_at']}",styles["BodyText"]),Spacer(1,12)]
    sections=[("Executive Summary",f"Recommended architecture: {snap['recommendation']['recommended_option']}. Overall fit score: {snap['recommendation']['overall_score']}. Confidence: {snap['recommendation']['confidence']['label']} ({snap['recommendation']['confidence']['value']:.0%}). Estimated stored-price range: {_money(snap['recommendation']['estimated_cost'])}."),("Project Details",f"Mode: {snap['project']['mode']} | Region: {snap['project'].get('target_region') or 'Not provided'} | Website: {snap['project'].get('website_url') or 'Not live'}"),("Technology Detection","; ".join(f"{t['category']}: {t['technology']} ({t['confidence']:.0%})" for t in snap['technology']) or "No live technology evidence available."),("Performance","; ".join(f"{p['strategy']}: {p.get('performance_score') if p.get('performance_score') is not None else 'Unavailable'}" for p in snap['performance'])),("Workload",f"Estimated RPS: {snap['workload'].get('estimated_rps','n/a')}; Peak RPS: {snap['workload'].get('peak_rps','n/a')}; Class: {snap['workload'].get('classification','n/a')}."),("Hosting Recommendation",f"{snap['recommendation']['recommended_option']} with resources {snap['recommendation']['resource_size']} and cost {_money(snap['recommendation']['estimated_cost'])}."),("Assumptions & Warnings","Assumptions: "+("; ".join(snap['recommendation'].get('assumptions',[])) or "None")+". Warnings: "+("; ".join(snap['recommendation'].get('warnings',[])) or "None"))]
    for title,text in sections: story += [Paragraph(title,styles["Heading2"]),Paragraph(str(text),styles["BodyText"]),Spacer(1,10)]
    story += [Paragraph("Optimization Plan",styles["Heading2"])]
    for o in snap.get("optimizations",[]): story += [Paragraph(f"{o['priority']} - {o['title']}",styles["Heading3"]),Paragraph(o['explanation'],styles["BodyText"]),Spacer(1,6)]
    doc.build(story)

def generate_report(db:Session,project:Project,user_id:str):
    if not project.latest_analysis_run_id: raise AppError("REPORT_GENERATION_FAILED","Run an analysis before generating a report.",409)
    snap=snapshot(db,project,project.latest_analysis_run_id); version=(db.scalar(select(func.count(Report.id)).where(Report.project_id==project.id)) or 0)+1
    row=Report(project_id=project.id,user_id=user_id,analysis_run_id=project.latest_analysis_run_id,version=version,snapshot=snap,status="READY"); db.add(row); db.flush(); filename=f"report-{project.id}-v{version}-{row.id}.pdf"; path=Path(settings.report_storage_dir)/filename
    render_pdf(snap,path); row.file_key=filename; db.commit(); return row
