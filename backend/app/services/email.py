from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("app.email")


class LogEmailProvider:
    """Mock provider: logs the email instead of sending it (local/dev default)."""

    def send(self, *, to: str, subject: str, body: str) -> bool:
        logger.info("EMAIL to=%s subject=%s body=%s", to, subject, body)
        return True


class ResendEmailProvider:
    def __init__(self, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.sender = sender

    def send(self, *, to: str, subject: str, body: str) -> bool:
        import resend

        resend.api_key = self.api_key
        resend.Emails.send(
            {
                "from": self.sender,
                "to": [to],
                "subject": subject,
                "text": body,
            }
        )
        return True


def get_email_provider() -> LogEmailProvider | ResendEmailProvider:
    if settings.EMAIL_PROVIDER == "resend" and settings.RESEND_API_KEY:
        return ResendEmailProvider(settings.RESEND_API_KEY, settings.EMAIL_FROM)
    return LogEmailProvider()


def send_email(*, to: Optional[str], subject: str, body: str) -> bool:
    recipient = to or settings.REMINDER_EMAIL or settings.EMAIL_FROM
    return get_email_provider().send(to=recipient, subject=subject, body=body)
