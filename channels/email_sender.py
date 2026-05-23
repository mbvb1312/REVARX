import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email via the Resend API.
    Returns True on success, False on failure.
    """
    try:
        from_email = os.getenv("FROM_EMAIL")
        if not from_email:
            from_email = "onboarding@resend.dev"

        # Format body as HTML paragraph for sleek rendering
        r = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": f"<p style='font-family: sans-serif; font-size: 14px; color: #333;'>{body}</p>"
        })
        
        return r is not None
    except Exception as exc:
        print(f"[email_sender] Failed to send email via Resend to {to_email}: {exc}")
        return False
