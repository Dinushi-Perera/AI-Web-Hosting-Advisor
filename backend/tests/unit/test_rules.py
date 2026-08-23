from app.services.rule_engine import evaluate
def test_low_skill_kubernetes_penalty():
    rules=evaluate({"budget":50,"kubernetesSkill":False,"category":"Blog"},{"peak_rps":10})
    assert any(r["rule_id"]=="R_K8S_LOW_SKILL" and r["score_delta"]<0 for r in rules)
