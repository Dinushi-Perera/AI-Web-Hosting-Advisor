from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from app.models import Project, ProjectInput, TechnologyDetection, TechnologyEvidence, PerformanceAudit, WorkloadEstimate, Recommendation, Optimization, Report, AnalysisRun, LoadTestPlan, LoadTestResult, TestResult, Feedback, AuditLog, Notification
from app.services.evaluation_service import evaluate_supplied_assets
from app.services.project_service import normalized_payload
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
    plans=list(db.scalars(select(LoadTestPlan).where(LoadTestPlan.project_id==project.id).order_by(LoadTestPlan.created_at.desc())))
    load_tests=[]
    for plan in plans:
        result=db.scalar(select(LoadTestResult).where(LoadTestResult.load_test_plan_id==plan.id).order_by(LoadTestResult.created_at.desc()))
        load_tests.append({"plan_id":plan.public_id,"analysis_run_id":plan.analysis_run_id,"test_type":plan.test_type,"target_url":plan.target_url,"authorization_confirmed":plan.authorization_confirmed,"risk_acknowledged":plan.risk_acknowledged,"expected_users":plan.expected_concurrent_users,"estimated_rps":plan.estimated_rps,"peak_rps":plan.peak_rps,"target_vus":plan.virtual_users,"stages":plan.stages,"thresholds":{"p95_ms":plan.response_time_threshold_ms,"error_rate":plan.error_rate_threshold},"result":{"peak_vus":result.peak_vus,"average_rps":result.average_rps,"p95_ms":result.http_req_duration_p95_ms,"p99_ms":result.http_req_duration_p99_ms,"error_rate":result.http_req_failed_rate,"checks_passed":result.checks_passed,"checks_failed":result.checks_failed,"status":result.overall_status,"ai_validation_status":result.ai_validation_status,"resource_metrics":(result.analysis_json or {}).get("resource_metrics",{}),"analysis":result.analysis_json} if result else None})
    tests=[row for row in db.scalars(select(TestResult).order_by(TestResult.executed_at.desc()).limit(250)) if not (row.details or {}).get("project_id") or (row.details or {}).get("project_id")==project.id];feedback=list(db.scalars(select(Feedback).where(Feedback.project_id==project.id)));evaluation=evaluate_supplied_assets()
    return {"project":{"id":project.id,"title":project.title,"mode":project.mode,"website_url":project.website_url,"currency":"USD"},"input":normalized_payload(inp.payload) if inp else {"currency":"USD"},"technology":tech,"performance":perf,"workload":{"concurrent_users":w.concurrent_users,"estimated_rps":w.estimated_rps,"peak_rps":w.peak_rps,"classification":w.classification,"database_intensity":w.database_intensity,"storage_gb":w.storage_gb,"bandwidth_gb":w.bandwidth_gb,"growth_level":w.growth_level,"assumptions":w.assumptions} if w else {},"recommendation":{"recommended_option":r.recommended_option,"overall_score":r.overall_score,"confidence":{"value":r.confidence_value,"label":r.confidence_label},"resource_size":r.resource_size,"estimated_cost":r.estimated_cost,"cost_optimization":r.cost_optimization,"decision_evidence":r.decision_evidence,"llm_explanation":r.llm_explanation,"llm_status":r.llm_status,"llm_model":r.llm_model or (r.llm_explanation or {}).get("configured_model"),"alternatives":r.alternatives,"reasons":r.reasons,"assumptions":r.assumptions,"warnings":r.warnings,"model_version":r.model_version},"optimizations":[{"priority":o.priority,"category":o.category,"title":o.title,"explanation":o.explanation,"difficulty":o.difficulty,"status":o.status,"steps":o.steps} for o in opts],"load_testing":load_tests,"testing":{"results":[{"type":x.test_type,"name":x.test_name,"status":x.status,"details":x.details} for x in tests],"feedbackCount":len(feedback),"evaluation":evaluation},"snapshot_generated_at":datetime.now(timezone.utc).isoformat()}

def _money(cost):
    if not cost or cost.get("min") is None:return "Unavailable"
    return f"USD {cost.get('min'):.2f} - {cost.get('max'):.2f} / month"

def _resource(resource):
    if not isinstance(resource,dict):return str(resource or "Unavailable")
    return f"{resource.get('vcpu','?')} vCPU, {resource.get('ram_gb','?')} GB RAM, {resource.get('storage_gb','?')} GB storage"

def _alternatives(items):
    if not items:return "No alternative scores were stored"
    summaries=[]
    for item in items:
        if not isinstance(item,dict):continue
        monthly=item.get("estimated_monthly_range") or [None,None]
        cost=_money({"min":monthly[0],"max":monthly[1]})
        summaries.append(f"{item.get('display_name') or item.get('option','Option')}: fit {item.get('score','n/a')}, {cost}")
    return "; ".join(summaries)

def render_pdf(snap:dict,path:Path):
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name="Small",parent=styles["BodyText"],fontSize=8,leading=11,textColor=colors.HexColor("#57534e")));styles.add(ParagraphStyle(name="TableHeader",parent=styles["Small"],textColor=colors.white));styles["Title"].textColor=colors.HexColor("#047857");styles["Heading2"].textColor=colors.HexColor("#065f46");doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=18*mm,bottomMargin=18*mm,title=f"AI Hosting Advisor - {snap['project']['title']}")
    story=[Paragraph("AI-Driven Web Hosting Advisor",styles["Title"]),Paragraph("Decision Report and Testing Evidence",styles["Heading2"]),Spacer(1,6),Paragraph(snap["project"]["title"],styles["Heading1"]),Paragraph(f"All costs are USD estimates. Generated {snap['snapshot_generated_at']}",styles["Small"]),Spacer(1,12)]
    reasons="; ".join(str(x.get("description") or x.get("note") or x) if isinstance(x,dict) else str(x) for x in snap['recommendation'].get('reasons',[])) or "The highest combined workload, budget, reliability and operational-fit score."
    sections=[("Executive Summary",f"Recommended architecture: {snap['recommendation']['recommended_option']}. Fit score: {snap['recommendation']['overall_score']}. Confidence: {snap['recommendation']['confidence']['label']} ({snap['recommendation']['confidence']['value']:.0%}). Estimated range: {_money(snap['recommendation']['estimated_cost'])}."),("Why This Is the Better Choice",reasons),("Project and Input Mode",f"Mode: {snap['project']['mode']}. Live URL modes use measured website evidence; Planned and New Idea modes clearly label performance as unavailable and rely on supplied requirements. Website: {snap['project'].get('website_url') or 'Not live'}."),("Technology Evidence","; ".join(f"{t['category']}: {t['technology']} ({t['confidence']:.0%})" for t in snap['technology']) or "No live technology evidence was available for this input mode."),("Performance Evidence","; ".join(f"{p['strategy']}: {p.get('performance_score') if p.get('performance_score') is not None else 'Unavailable'}" for p in snap['performance']) or "No measured performance evidence."),("Workload in Plain Language",f"Estimated normal traffic is {snap['workload'].get('estimated_rps','n/a')} requests/second and peak traffic is {snap['workload'].get('peak_rps','n/a')} requests/second. Classification: {snap['workload'].get('classification','n/a')}."),("Suggested Starting Size and Cost",f"Start with {_resource(snap['recommendation']['resource_size'])}. Estimated cost: {_money(snap['recommendation']['estimated_cost'])}. This is a starting point, not a guarantee; validate it with monitoring and authorized load testing."),("Alternatives and Benefits",f"VPS is simple and cost-effective for steady smaller workloads. Cloud VM offers flexible scaling and managed-service choices. Kubernetes offers strong orchestration for genuinely complex, high-scale teams but adds operational cost. Comparison: {_alternatives(snap['recommendation'].get('alternatives',[]))}."),("Assumptions and Warnings","Assumptions: "+("; ".join(snap['recommendation'].get('assumptions',[])) or "None")+". Warnings: "+("; ".join(snap['recommendation'].get('warnings',[])) or "None"))]
    for title,text in sections: story += [Paragraph(title,styles["Heading2"]),Paragraph(str(text),styles["BodyText"]),Spacer(1,10)]
    evidence=snap["recommendation"].get("decision_evidence") or {};classifier=evidence.get("classifier") or {};resource=evidence.get("resource_sizer") or {};llm=snap["recommendation"].get("llm_explanation") or {};llm_content=llm.get("content") or {};cost_opt=snap["recommendation"].get("cost_optimization") or {}
    story += [Paragraph("Model Decision Evidence",styles["Heading2"]),Paragraph(f"Classifier: {classifier.get('version','unavailable')} ({classifier.get('source','unknown')}) predicted {classifier.get('output','n/a')}. Resource model: {resource.get('version','unavailable')} ({resource.get('source','unknown')}). LLM explanation status: {llm.get('status','NOT_CONFIGURED')} using {llm.get('model') or 'deterministic template'}. The Logistic Regression classifier alone selects the hosting option; resource sizing, pricing, and the LLM cannot change it.",styles["BodyText"]),Spacer(1,8)]
    if llm_content.get("summary"):story += [Paragraph("AI Explanation",styles["Heading3"]),Paragraph(escape(llm_content["summary"]),styles["BodyText"]),Paragraph(escape(llm_content.get("cost_explanation","") or ""),styles["BodyText"]),Spacer(1,8)]
    story += [Paragraph("Cost Optimization Evidence",styles["Heading3"]),Paragraph(f"Method: {cost_opt.get('method','unavailable')}. Budget tier: {cost_opt.get('budget_tier','unavailable')}. Savings status: {cost_opt.get('savings_status','unavailable')}. Estimated monthly savings: {cost_opt.get('estimated_monthly_savings') if cost_opt.get('estimated_monthly_savings') is not None else 'not calculated because current cost was not supplied'}.",styles["BodyText"]),Spacer(1,10)]
    measured=[item for item in snap.get("performance",[]) if item.get("status")=="AVAILABLE"]
    for item in measured:
        metrics=item.get("metrics") or {};cwv=metrics.get("core_web_vitals") or {};sources=metrics.get("metric_sources") or {};opportunities=metrics.get("opportunities") or []
        story += [Paragraph(f"{item['strategy'].title()} Core Web Vitals and Lighthouse Evidence",styles["Heading2"]),Paragraph(f"Overall Core Web Vitals status: {cwv.get('overall_status','INSUFFICIENT_DATA')}. LCP {metrics.get('lcp_ms','n/a')} ms ({sources.get('lcp_ms','UNAVAILABLE')}), INP {metrics.get('inp_ms','n/a')} ms ({sources.get('inp_ms','UNAVAILABLE')}), CLS {metrics.get('cls','n/a')} ({sources.get('cls','UNAVAILABLE')}). Field evidence represents real-user experience when available; Lighthouse values are controlled lab observations.",styles["BodyText"])]
        if opportunities:story += [Paragraph("Highest-impact opportunities: "+"; ".join(f"{row.get('title')} ({row.get('display_value') or str(row.get('savings_ms',0))+' ms potential savings'})" for row in opportunities[:5]),styles["BodyText"])]
        story += [Spacer(1,10)]
    planned_performance=[p for p in snap.get("performance",[]) if p.get("status")=="PLANNED"]
    if planned_performance:
        targets=planned_performance[0].get("metrics") or {}
        story += [Paragraph("Pre-launch Performance Budget",styles["Heading2"]),Paragraph(f"This project is not live, so no measured Lighthouse score is claimed. Development targets are: LCP at or below {targets.get('target_lcp_ms','n/a')} ms, INP at or below {targets.get('target_inp_ms','n/a')} ms, CLS at or below {targets.get('target_cls','n/a')}, initial JavaScript at or below {targets.get('initial_js_kb','n/a')} KB, API p95 at or below {targets.get('api_p95_ms','n/a')} ms, and error rate below {float(targets.get('target_error_rate',0))*100:.1f}%.",styles["BodyText"]),Spacer(1,10)]
    budget=snap.get("input",{}).get("budget") or snap.get("input",{}).get("monthly_budget");estimated=snap.get("recommendation",{}).get("estimated_cost") or {};maximum=estimated.get("max")
    if budget not in (None,"") and maximum is not None:
        budget_value=float(budget);budget_status="within budget" if maximum<=budget_value else "partially within budget" if estimated.get("min") is not None and estimated.get("min")<=budget_value else "over budget"
        story += [Paragraph("Budget Compatibility",styles["Heading2"]),Paragraph(f"User budget: USD {budget_value:.2f} per month. Estimated range: {_money(estimated)}. Result: {budget_status}. The Cost Explorer shows the provider plans and component breakdown behind this comparison.",styles["BodyText"]),Spacer(1,10)]
    story += [Paragraph("Load Test Planning & Execution Evidence",styles["Heading2"])]
    if not snap.get("load_testing"):story += [Paragraph("No authorized load-test plan or imported execution evidence is available.",styles["BodyText"]),Spacer(1,10)]
    for item in snap.get("load_testing",[]):
        story += [Paragraph(f"{item['test_type']} plan - {item['target_vus']} target VUs",styles["Heading3"]),Paragraph(f"Authorization confirmed: {item['authorization_confirmed']}; risk acknowledged: {item['risk_acknowledged']}. Expected users: {item['expected_users']}; estimated/peak RPS: {item['estimated_rps']} / {item['peak_rps']}. Thresholds: p95 &lt; {item['thresholds']['p95_ms']} ms, errors &lt; {item['thresholds']['error_rate']:.2%}.",styles["BodyText"])]
        result=item.get("result")
        if result:
            monitoring=result.get("resource_metrics") or {}
            monitoring_text=f" Optional monitoring evidence: {monitoring}." if monitoring else " No optional server monitoring evidence was supplied."
            story += [Paragraph(f"Imported evidence: {result['status']}; peak VUs {result['peak_vus']}; average RPS {result['average_rps']}; p95 {result['p95_ms']} ms; p99 {result['p99_ms']} ms; errors {result['error_rate']:.2%}; AI/resource validation {result['ai_validation_status']}.{monitoring_text}",styles["BodyText"]),Paragraph("This evidence applies only to the tested scenario and does not permanently prove production capacity.",styles["BodyText"])]
        else:story += [Paragraph("The script has not been manually executed and imported; no result is claimed.",styles["BodyText"])]
        story += [Spacer(1,8)]
    story += [Paragraph("Optimization Plan",styles["Heading2"])]
    for o in snap.get("optimizations",[]): story += [Paragraph(f"{o['priority']} - {o['title']}",styles["Heading3"]),Paragraph(o['explanation'],styles["BodyText"]),Spacer(1,6)]
    story += [PageBreak(),Paragraph("Testing Strategy and Evaluation",styles["Heading2"]),Paragraph("UT tests isolated functions. IT checks service and database integration. ST checks complete workflows. UAT uses genuine user ratings. ORT checks demo and deployment readiness.",styles["BodyText"]),Spacer(1,8)]
    cell=lambda value,header=False:Paragraph(escape(str(value)),styles["TableHeader" if header else "Small"])
    test_rows=[[cell("Type",True),cell("Test case",True),cell("Status",True),cell("Meaning",True)]]+[[cell(x["type"]),cell(x["name"]),cell(x["status"]),cell((x.get("details") or {}).get("plainLanguage","Stored test evidence"))] for x in snap.get("testing",{}).get("results",[])[:20]]
    table=Table(test_rows,colWidths=[18*mm,47*mm,24*mm,78*mm],repeatRows=1);table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#047857")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.HexColor("#a8a29e")),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f5f4")]) ]));story += [table,Spacer(1,10)]
    ev=snap.get("testing",{}).get("evaluation",{});c=ev.get("classifier",{});rs=ev.get("resource",{});story += [Paragraph("Measured Model Evaluation",styles["Heading2"]),Paragraph(f"The supplied classifier and resource datasets contain 5,000 rows each. Evaluation uses {ev.get('validationRows',0)} separate cases. Classifier accuracy {c.get('accuracy',0):.2%}, precision {c.get('precision',0):.2%}, recall {c.get('recall',0):.2%}, F1 {c.get('f1',0):.2%}. Resource errors: vCPU MAE {rs.get('vcpuMae',0):.3f}, RAM MAE {rs.get('ramMae',0):.3f} GB; R-squared {rs.get('vcpuR2',0):.3f}/{rs.get('ramR2',0):.3f}. UAT responses for this project: {snap.get('testing',{}).get('feedbackCount',0)}.",styles["BodyText"]),Spacer(1,8),Paragraph("Decision boundary: this advisor supports a human decision. Prices change, synthetic training data has limits, live measurements can vary, and a passing load test applies only to the tested scenario.",styles["Small"])]
    def footer(canvas,document):canvas.saveState();canvas.setFont("Helvetica",8);canvas.setFillColor(colors.HexColor("#57534e"));canvas.drawString(16*mm,10*mm,"AI Web Hosting Advisor - Decision Support");canvas.drawRightString(194*mm,10*mm,f"Page {document.page}");canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def generate_report(db:Session,project:Project,user_id:str):
    if not project.latest_analysis_run_id: raise AppError("REPORT_GENERATION_FAILED","Run an analysis before generating a report.",409)
    snap=snapshot(db,project,project.latest_analysis_run_id); version=(db.scalar(select(func.count(Report.id)).where(Report.project_id==project.id)) or 0)+1
    row=Report(project_id=project.id,user_id=user_id,analysis_run_id=project.latest_analysis_run_id,version=version,snapshot=snap,status="READY"); db.add(row); db.flush(); filename=f"report-{project.id}-v{version}-{row.id}.pdf"; path=Path(settings.report_storage_dir)/filename
    render_pdf(snap,path);row.file_key=filename;db.add(AuditLog(actor_user_id=user_id,action="REPORT_GENERATED",entity_type="PROJECT",entity_id=project.id,metadata_json={"report_id":row.id,"version":version}));db.add(Notification(user_id=user_id,type="REPORT_READY",title="Report ready",message=f"Version {version} of {project.title} is ready.",data={"project_id":project.id,"report_id":row.id,"version":version}));db.commit(); return row

def refresh_report_evidence(db:Session,project:Project,row:Report):
    """Refresh the same report version after project-specific tests are persisted."""
    snap=snapshot(db,project,row.analysis_run_id);path=Path(settings.report_storage_dir)/row.file_key
    render_pdf(snap,path);row.snapshot=snap;db.commit();return row
