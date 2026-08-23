from app.core.config import settings
from app.services import mail_service


class FakeSMTP:
    sent = None

    def __init__(self, host, port, timeout):
        assert host == "smtp.example.com"
        assert port == 587
        assert timeout == 15

    def __enter__(self): return self
    def __exit__(self, *_): return False
    def starttls(self): pass
    def login(self, username, password):
        assert (username,password) == ("sender@example.com","app-password")
    def send_message(self, message):
        FakeSMTP.sent = message


def test_password_reset_email_contains_single_use_link(monkeypatch):
    monkeypatch.setattr(settings,"smtp_host","smtp.example.com")
    monkeypatch.setattr(settings,"smtp_port",587)
    monkeypatch.setattr(settings,"smtp_username","sender@example.com")
    monkeypatch.setattr(settings,"smtp_password","app-password")
    monkeypatch.setattr(settings,"smtp_from_email","sender@example.com")
    monkeypatch.setattr(settings,"smtp_use_tls",True)
    monkeypatch.setattr(settings,"smtp_use_ssl",False)
    monkeypatch.setattr(settings,"frontend_url","http://localhost:3000")
    monkeypatch.setattr(mail_service.smtplib,"SMTP",FakeSMTP)

    mail_service.send_password_reset_email("user@example.com","Test User","reset-token")

    assert FakeSMTP.sent["To"] == "user@example.com"
    assert "Reset your AI Hosting Advisor password" == FakeSMTP.sent["Subject"]
    plain = FakeSMTP.sent.get_body(preferencelist=("plain",)).get_content()
    assert "http://localhost:3000/reset-password?token=reset-token" in plain
