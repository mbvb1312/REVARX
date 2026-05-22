import os

from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email via SendGrid.
    Returns True on success, False on failure.
    """
    try:
        message = Mail(
            from_email=os.getenv("FROM_EMAIL"),
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = client.send(message)
        return response.status_code in [200, 201, 202]
    except Exception as exc:
        print(f"[email_sender] Failed to send to {to_email}: {exc}")
        return False
