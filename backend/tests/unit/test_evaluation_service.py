from app.services.evaluation_service import evaluate_supplied_assets


def test_supplied_dataset_and_model_evaluation_is_complete():
    result = evaluate_supplied_assets()
    rows = {item["name"]: item["rows"] for item in result["datasets"]}

    assert rows["hosting_advisor_master_5000.csv"] == 5000
    assert rows["hosting_classifier_5000.csv"] == 5000
    assert rows["resource_sizing_5000.csv"] == 5000
    assert rows["independent_validation_cases_300.csv"] == 300
    assert result["validationRows"] == 300
    assert 0 <= result["classifier"]["accuracy"] <= 1
    assert 0 <= result["classifier"]["f1"] <= 1
    assert result["classifier"]["featureImportance"][0]["importance"] > 0
    assert len(result["classifier"]["confusionMatrix"]) == len(result["classifier"]["labels"])
    assert result["resource"]["vcpuMae"] >= 0
    assert result["resource"]["ramMae"] >= 0
    assert result["resource"]["vcpuR2"] <= 1
    assert result["resource"]["ramR2"] <= 1
