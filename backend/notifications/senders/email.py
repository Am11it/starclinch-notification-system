"""Email via Resend. Docs: https://resend.com/docs/send-with-python

Without your own domain, send from onboarding@resend.dev — Resend then only
delivers to the email you signed up to Resend with.
"""

import resend
from django.conf import settings
from django.utils.html import escape


def send_email(to_email, subject, body):
    if not settings.RESEND_API_KEY:
        return False, "RESEND_API_KEY not set in .env"

    resend.api_key = settings.RESEND_API_KEY
    try:
        result = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": "<p>" + escape(body).replace("\n", "<br>") + "</p>",
            "text": body,
        })
        return True, f"Sent via Resend: {result}"
    except resend.exceptions.ResendError as error:
        return False, f"Resend error: {error}"
