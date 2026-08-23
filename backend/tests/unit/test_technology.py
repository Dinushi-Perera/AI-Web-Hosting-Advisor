from app.services.technology_detector import detect_from_response
def test_next_and_cloudflare_detection():
    rows=detect_from_response({"headers":{"server":"cloudflare","cf-ray":"x"},"content":b'<html><script id="__NEXT_DATA__"></script><script src="/_next/static/a.js"></script></html>'})
    assert any(x["technology"]=="Next.js" and x["confidence"]>=.8 for x in rows)
    assert any(x["technology"]=="Cloudflare" for x in rows)
