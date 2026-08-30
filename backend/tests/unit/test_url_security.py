import pytest
import httpx

from app.core.exceptions import AppError
from app.services import url_security_service


def test_public_hostname_is_allowed(monkeypatch):
    monkeypatch.setattr(url_security_service, "_host_ips", lambda host: {"203.0.113.10"})
    monkeypatch.setattr(url_security_service, "_safe_ip", lambda value: value == "203.0.113.10")

    assert url_security_service.validate_public_url("https://example.com/path") == "https://example.com/path"


@pytest.mark.parametrize("url", ["http://127.0.0.1", "http://10.0.0.4", "http://[::1]"])
def test_private_ip_literals_are_blocked(url):
    with pytest.raises(AppError) as caught:
        url_security_service.validate_public_url(url)

    assert caught.value.code == "URL_BLOCKED"


@pytest.mark.parametrize(
    ("transport_error", "expected_code"),
    [
        (httpx.ReadTimeout("timed out"), "URL_FETCH_TIMEOUT"),
        (httpx.ConnectError("connection failed"), "URL_UNREACHABLE"),
    ],
)
def test_safe_fetch_converts_transport_failures_to_public_errors(monkeypatch, transport_error, expected_code):
    class FailingClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def stream(self, method, url):
            raise transport_error

    monkeypatch.setattr(url_security_service, "validate_public_url", lambda url: url)
    monkeypatch.setattr(url_security_service.httpx, "Client", FailingClient)

    with pytest.raises(AppError) as caught:
        url_security_service.safe_fetch("https://example.com")

    assert caught.value.code == expected_code
