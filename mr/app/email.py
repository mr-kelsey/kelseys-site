from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import SiteConfig


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailSender(EmailSender):
    """Prints the email instead of sending it — used for local dev and tests."""

    def __init__(self) -> None:
        self.sent_messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.sent_messages.append(message)
        print(f"[email] to={message.to} subject={message.subject}\n{message.body}")


class ResendEmailSender(EmailSender):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def send(self, message: EmailMessage) -> None:
        import resend

        resend.api_key = self._api_key
        resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": message.to,
                "subject": message.subject,
                "text": message.body,
            }
        )


def _build_site_email_sender() -> EmailSender:
    config = SiteConfig()
    if config.resend_api_key:
        return ResendEmailSender(api_key=config.resend_api_key)
    return ConsoleEmailSender()


site_email_sender: EmailSender = _build_site_email_sender()
