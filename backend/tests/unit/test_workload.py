from app.services.workload_estimator import estimate
def test_workload_is_deterministic():
    r=estimate({"concurrentUsers":120,"requestsPerUser":10,"peakMultiplier":2,"storage":100,"dbWorkload":"Medium"},"PLANNED")
    assert r["estimated_rps"]==20
    assert r["peak_rps"]==40
    assert r["classification"]=="MEDIUM"
