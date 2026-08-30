import pytest

from app.core.exceptions import AppError
from app.services import analysis_pipeline


@pytest.mark.parametrize(
    "error_code",
    ["URL_UNREACHABLE", "URL_FETCH_TIMEOUT", "URL_RESPONSE_TOO_LARGE", "URL_TOO_MANY_REDIRECTS"],
)
def test_live_evidence_failure_does_not_abort_analysis(monkeypatch, error_code):
    monkeypatch.setattr(analysis_pipeline, "validate_public_url", lambda url: url)
    monkeypatch.setattr(
        analysis_pipeline,
        "safe_fetch",
        lambda url: (_ for _ in ()).throw(AppError(error_code, "Evidence unavailable.", 400)),
    )

    url, response, warning = analysis_pipeline.collect_live_evidence("https://example.com")

    assert url == "https://example.com"
    assert response is None
    assert error_code in warning
    assert "confidence was reduced" in warning


def test_live_evidence_security_failure_still_aborts_analysis(monkeypatch):
    monkeypatch.setattr(
        analysis_pipeline,
        "validate_public_url",
        lambda url: (_ for _ in ()).throw(AppError("URL_BLOCKED", "Unsafe target.", 400)),
    )

    with pytest.raises(AppError) as caught:
        analysis_pipeline.collect_live_evidence("http://127.0.0.1")

    assert caught.value.code == "URL_BLOCKED"
