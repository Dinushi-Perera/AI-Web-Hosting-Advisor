from app.services.rule_engine import evaluate
def test_runtime_rules_cannot_adjust_hosting_selection():
    rules=evaluate({"budget":50,"kubernetesSkill":False,"category":"Blog"},{"peak_rps":10})
    assert rules == []
