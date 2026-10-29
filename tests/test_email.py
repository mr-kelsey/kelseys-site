from app.email import ConsoleEmailSender, EmailMessage, EmailSender, ResendEmailSender


def test_console_email_sender_records_sent_message() -> None:
    sender = ConsoleEmailSender()
    message = EmailMessage(to="a@example.com", subject="Hi", body="Hello")
    sender.send(message)
    assert sender.sent_messages == [message]


def test_console_email_sender_is_an_email_sender() -> None:
    assert isinstance(ConsoleEmailSender(), EmailSender)


def test_resend_email_sender_is_an_email_sender() -> None:
    assert isinstance(ResendEmailSender(api_key="key"), EmailSender)
