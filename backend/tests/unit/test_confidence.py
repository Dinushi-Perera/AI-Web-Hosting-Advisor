from app.services.confidence_service import calculate
def test_confidence_range():
    r=calculate(.8,.8,.8,.8,.8,.8)
    assert 0<=r["value"]<=1
    assert r["label"] in {"HIGH","MEDIUM","LOW","INSUFFICIENT_DATA"}
