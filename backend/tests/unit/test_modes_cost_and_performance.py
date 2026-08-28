import pytest
from pydantic import ValidationError

from app.schemas.project import IdeaFrontendRequest, PlannedFrontendRequest
from app.services.performance_service import _audit_from_lighthouse, metric_status, planned_budget
from app.services.scoring_service import cost_fit, score_options
from app.services.clarification_service import apply_answers, questions
from app.services.optimization_service import generate as generate_optimizations
from app.services.pricing_service import PricingService


def test_planned_and_idea_inputs_validate_real_budget_context():
    planned=PlannedFrontendRequest(projectName="Learning platform",websiteType="Education",budget="80",concurrentUsers="",monthlyUsers="")
    idea=IdeaFrontendRequest(idea="A booking platform for local service businesses",industry="SaaS",targetUsers="Local businesses",features=["Login","Bookings"],traffic="Growing business",budget="100",timeline="3-6 months",experience="Intermediate")
    assert planned.budget == 80
    assert planned.concurrentUsers is None
    assert idea.budget == 100
    with pytest.raises(ValidationError):
        IdeaFrontendRequest(idea="Too short",industry="SaaS",targetUsers="Users",features=[],traffic="Small",budget=-1,timeline="Soon",experience="Beginner")


def test_planned_modes_receive_targets_not_fake_measurements():
    rows=planned_budget({"websiteType":"E-commerce","audience":"Growing business"},"PLANNED")
    assert {row["status"] for row in rows} == {"PLANNED"}
    assert all(row["performance_score"] is None for row in rows)
    assert rows[0]["metrics"]["target_lcp_ms"] == 2500
    assert rows[0]["metrics"]["target_error_rate"] == 0.01


def test_budget_scoring_uses_stored_option_costs():
    ml={"probabilities":{"VPS":.34,"CLOUD_VM":.33,"KUBERNETES":.33}}
    costs={"VPS":{"min":35,"max":45},"CLOUD_VM":{"min":95,"max":120},"KUBERNETES":{"min":220,"max":300}}
    scores=score_options({"peak_rps":25},{"budget":50,"kubernetesSkill":False},ml,[],costs)
    by_option={row["option"]:row for row in scores}
    assert by_option["VPS"]["budget_fit"] == 100
    assert by_option["CLOUD_VM"]["budget_fit"] < by_option["VPS"]["budget_fit"]
    assert by_option["KUBERNETES"]["budget_fit"] == 0


def test_ranking_exposes_cost_ranges_weights_rules_and_rank():
    ml={"probabilities":{"VPS":.34,"CLOUD_VM":.33,"KUBERNETES":.33}}
    costs={"VPS":{"min":45,"max":120},"CLOUD_VM":{"min":70,"max":78},"KUBERNETES":{"min":180,"max":260}}
    rows=score_options({"peak_rps":120},{"budget":80,"kubernetesSkill":False},ml,[{"option":"CLOUD_VM","score_delta":8,"reason":"Growth","rule_id":"T","effect":"BOOST"}],costs)
    assert [row["rank"] for row in rows] == [1,2,3]
    assert rows[0]["score_breakdown"]["final_score"] == rows[0]["score"]
    assert rows[0]["score_breakdown"]["weights"].get("budget",0) == 0
    assert rows[0]["score_breakdown"]["weights"]["trained_logistic_regression_probability"] == 1
    by_option={row["option"]:row for row in rows}
    assert by_option["VPS"]["cost_analysis"]["status"] == "PARTIALLY_WITHIN_BUDGET"
    assert by_option["CLOUD_VM"]["cost_analysis"]["status"] == "WITHIN_BUDGET"
    assert by_option["KUBERNETES"]["cost_analysis"]["status"] == "OVER_BUDGET"


def test_missing_pricing_is_explicit_and_not_fabricated():
    result=cost_fit({},100)
    assert result["status"] == "PRICING_UNAVAILABLE"
    assert result["range"] == {"min":None,"max":None}
    assert result["evidence"] == "UNAVAILABLE"


def test_large_model_size_uses_labelled_stored_price_extrapolation():
    service=PricingService.__new__(PricingService)
    stored=[{"id":"p1","provider":"Provider A","plan":"8 GB","architecture":"CLOUD_VM","vcpu":4,"ramGb":8,"storageGb":100,"monthlyRange":[55,80],"currency":"USD","updatedAt":"2026-08-25T00:00:00+00:00","source":"Stored snapshot","isDemo":False,"isStale":False,"freshnessWarning":None}]
    service.list_plans=lambda architecture:stored
    rows=service.options("CLOUD_VM",16,32)
    assert rows[0]["isEstimate"] is True
    assert rows[0]["pricingMethod"] == "RESOURCE_RATIO_EXTRAPOLATION"
    assert rows[0]["scaleFactor"] == 4
    assert rows[0]["monthlyRange"] == [220,320]
    assert rows[0]["vcpu"] == 16 and rows[0]["ramGb"] == 32


def test_pagespeed_separates_crux_field_data_from_lighthouse_lab_metrics():
    payload={"loadingExperience":{"id":"https://example.com","metrics":{"LARGEST_CONTENTFUL_PAINT_MS":{"percentile":2200,"category":"FAST"},"INTERACTION_TO_NEXT_PAINT":{"percentile":180,"category":"FAST"},"CUMULATIVE_LAYOUT_SHIFT_SCORE":{"percentile":8,"category":"FAST"}}},"originLoadingExperience":{},"lighthouseResult":{"lighthouseVersion":"12.0","fetchTime":"2026-08-25T00:00:00Z","requestedUrl":"https://example.com","finalUrl":"https://example.com/","categories":{"performance":{"score":.91},"accessibility":{"score":.95},"best-practices":{"score":.88},"seo":{"score":.93}},"audits":{"largest-contentful-paint":{"numericValue":3100},"cumulative-layout-shift":{"numericValue":.18},"first-contentful-paint":{"numericValue":1700},"total-blocking-time":{"numericValue":180},"speed-index":{"numericValue":2900},"unused-javascript":{"title":"Reduce unused JavaScript","description":"Remove unused code","score":.4,"details":{"overallSavingsMs":450,"overallSavingsBytes":20480}}}}}
    result=_audit_from_lighthouse(payload,"mobile")
    assert result["performance_score"] == 91
    assert result["metrics"]["lcp_ms"] == 2200
    assert result["metrics"]["lab_metrics"]["lcp_ms"] == 3100
    assert result["metrics"]["cls"] == .08
    assert result["metrics"]["metric_sources"]["inp_ms"] == "CRUX_PAGE_FIELD"
    assert result["metrics"]["core_web_vitals"]["overall_status"] == "PASSED"
    assert result["metrics"]["opportunities"][0]["savings_ms"] == 450
    assert metric_status("INP",501) == "POOR"


def test_dynamic_clarifications_feed_canonical_sizing_inputs():
    payload={"traffic":"Growing business","budget":100,"clarifications":{"concurrentUsers":"240","storage":"180","dbWorkload":"High"}}
    asked=questions(payload)
    assert {item["key"] for item in asked} == {"concurrentUsers","storage","dbWorkload"}
    merged=apply_answers(payload)
    assert merged["concurrentUsers"] == "240"
    assert merged["storage"] == "180"
    assert merged["dbWorkload"] == "High"


def test_optimization_plan_covers_cost_performance_security_and_monitoring():
    performance=[{"strategy":"MOBILE","metrics":{"lcp_ms":4100}}]
    rows=generate_optimizations(performance,[],{"database_intensity":"HIGH"},"CLOUD_VM")
    categories={row["category"] for row in rows}
    assert {"FRONTEND","CACHE_CDN","DATABASE","COST","SECURITY","MONITORING"}.issubset(categories)
