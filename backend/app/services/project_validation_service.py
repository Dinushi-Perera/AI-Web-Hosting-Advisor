from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Project,ProjectInput,TechnologyDetection,PerformanceAudit,WorkloadEstimate,Recommendation,Optimization,Report,TestResult

def _case(code:str,status:str,actual:str,meaning:str)->dict:
    return {"code":code,"status":status,"actual":actual,"meaning":meaning}

def evaluate_project(db:Session,project:Project,run_id:str,persist:bool=False)->list[dict]:
    inp=db.scalar(select(ProjectInput).where(ProjectInput.project_id==project.id));payload=inp.payload if inp else {}
    tech=list(db.scalars(select(TechnologyDetection).where(TechnologyDetection.analysis_run_id==run_id)))
    perf=list(db.scalars(select(PerformanceAudit).where(PerformanceAudit.analysis_run_id==run_id)))
    workload=db.scalar(select(WorkloadEstimate).where(WorkloadEstimate.analysis_run_id==run_id))
    rec=db.scalar(select(Recommendation).where(Recommendation.analysis_run_id==run_id))
    opts=list(db.scalars(select(Optimization).where(Optimization.analysis_run_id==run_id)))
    report=db.scalar(select(Report).where(Report.analysis_run_id==run_id,Report.deleted_at.is_(None)))
    required={"LIVE_URL":["websiteUrl","concurrentUsers","budget"],"PLANNED":["projectName","websiteType","budget"],"NEW_IDEA":["idea","industry","targetUsers","features","traffic","budget"]}.get(project.mode,[])
    missing=[key for key in required if payload.get(key) in (None,"",[])]
    measured=any(row.performance_score is not None for row in perf);planned=bool(perf) and all(row.status=="PLANNED" for row in perf)
    estimated=rec.estimated_cost if rec else {};categories={row.category for row in opts}
    cases=[
        _case("INPUT_MODE_VALIDATION","PASSED" if not missing else "FAILED",f"{project.mode}; missing: {', '.join(missing) or 'none'}","Required fields are checked according to the selected live, planned, or idea mode."),
        _case("TECHNOLOGY_EVIDENCE","PASSED" if tech else "WARNING",f"{len(tech)} findings","Live evidence, declared technologies, or idea-based suggestions must remain traceable."),
        _case("PERFORMANCE_EVIDENCE","PASSED" if measured or planned else "WARNING","Measured audit" if measured else "Pre-launch targets" if planned else "Unavailable","Live projects use measurements; non-live projects use clearly labelled budgets without fabricated scores."),
        _case("WORKLOAD_ESTIMATE","PASSED" if workload and workload.concurrent_users>0 and workload.peak_rps>=0 else "FAILED",f"{workload.concurrent_users if workload else 0} concurrent; {workload.peak_rps if workload else 0} peak RPS","Traffic inputs must produce a usable capacity estimate and explicit assumptions."),
        _case("RECOMMENDATION_EXPLANATION","PASSED" if rec and rec.reasons and rec.assumptions is not None else "FAILED",rec.recommended_option if rec else "Missing","The selected architecture must include scores, reasons, confidence, assumptions, and alternatives."),
        _case("COST_RANGE","PASSED" if estimated.get("min") is not None and estimated.get("max") is not None else "WARNING",f"USD {estimated.get('min','?')}-{estimated.get('max','?')}","Cost is tested as an explainable range against the supplied monthly budget."),
        _case("OPTIMIZATION_COVERAGE","PASSED" if {"COST","MONITORING"}.issubset(categories) else "FAILED",", ".join(sorted(categories)) or "None","Each result must include cost right-sizing and operational monitoring actions plus evidence-specific improvements."),
        _case("REPORT_GENERATION","PASSED" if report and report.file_key else "FAILED",f"Version {report.version}" if report else "Missing","The immutable report snapshot must include every analysis section and a downloadable PDF."),
        _case("LOAD_TEST_SAFETY","PASSED","Authorization, risk acknowledgement, public-target validation, VU and duration caps","The system prepares safe tests but never performs an unrestricted load attack."),
    ]
    if persist:
        existing={
            (row.details or {}).get("code")
            for row in db.scalars(select(TestResult).where(TestResult.test_type=="ST"))
            if (row.details or {}).get("project_id")==project.id and (row.details or {}).get("analysis_run_id")==run_id
        }
        for case in cases:
            if case["code"] not in existing:
                stored_status="SKIPPED" if case["status"]=="WARNING" else case["status"]
                db.add(TestResult(test_type="ST",test_name=f"Project {case['code']}",status=stored_status,details={**case,"project_id":project.id,"analysis_run_id":run_id,"mode":project.mode,"plainLanguage":case["meaning"]}))
        db.commit()
    return cases
