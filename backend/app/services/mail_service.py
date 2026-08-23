import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import quote

from app.core.config import settings
from app.core.exceptions import AppError


def password_reset_url(token: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/reset-password?token={quote(token, safe='')}"


def send_password_reset_email(recipient: str, full_name: str, token: str) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        if settings.password_reset_return_token:
            return
        raise AppError(
            "EMAIL_NOT_CONFIGURED",
            "Password reset email is not configured. Configure the SMTP settings and try again.",
            503,
        )

    link = password_reset_url(token)
    message = EmailMessage()
    message["Subject"] = "Reset your AI Hosting Advisor password"
    message["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
    message["To"] = recipient
    message.set_content(
        f"Hello {full_name},\n\n"
        "Use the link below to reset your password. "
        f"The link expires in {settings.password_reset_minutes} minutes and can be used once.\n\n"
        f"{link}\n\n"
        "If you did not request this reset, you can ignore this email."
    )
    message.add_alternative(
        f"<p>Hello {full_name},</p>"
        f"<p>Use the button below to reset your password. The link expires in {settings.password_reset_minutes} minutes and can be used once.</p>"
        f'<p><a href="{link}" style="display:inline-block;padding:12px 18px;background:#4f46e5;color:#fff;text-decoration:none;border-radius:8px">Reset your password</a></p>'
        "<p>If you did not request this reset, you can ignore this email.</p>",
        subtype="html",
    )

    try:
        smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_class(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise AppError("EMAIL_SEND_FAILED", "The reset email could not be sent. Please try again.", 503) from exc
