"""
The heart of the system:
  fire_trigger("login", user)  ->  finds the enabled templates for "login"
                                   and sends each one on its channel.
"""

import re
import threading
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone

from .models import NotificationLog, Template, Trigger, WhatsAppStatus
from .senders import email, webpush, whatsapp

# Matches {{name}}, {{ email }}, ...
VARIABLE = re.compile(r"{{\s*(\w+)\s*}}")
# Meta's message id in a send response: "id":"wamid.HBgM..."
MESSAGE_ID = re.compile(r'"id":"(wamid\.[^"]+)"')

# Variables admins can use in any template, with example values (Meta needs examples).
VARIABLES = {
    "name": "John",
    "email": "john@example.com",
    "phone": "919876543210",
    "trigger": "Login",
    "time": "10 Oct 2026, 10:30",
    "site_name": "StarClinch",
}


def build_context(user, trigger):
    profile = getattr(user, "profile", None)
    return {
        "name": user.first_name or user.email.split("@")[0],
        "email": user.email,
        "phone": profile.phone if profile else "",
        "trigger": trigger.name,
        "time": timezone.now().strftime("%d %b %Y, %H:%M UTC"),
        "site_name": "StarClinch",
    }


def render(text, context):
    """'Hi {{name}}' + {'name': 'Amit'} -> 'Hi Amit'"""
    return VARIABLE.sub(lambda m: str(context.get(m.group(1), m.group(0))), text or "")


# ---------- Sending ----------

def send_one(template, user, is_test=False, phone=None, to_email=None):
    """Send one template to one user. Returns (success, detail) and writes a log row."""
    context = build_context(user, template.trigger)
    body = render(template.body, context)
    recipient = ""

    if template.channel == Template.WHATSAPP:
        recipient = phone or context["phone"]
        if not recipient:
            success, detail = False, "User has no phone number"
        elif template.wa_status == "APPROVED":
            params = [context.get(name, "") for name in template.wa_variables]
            success, detail = whatsapp.send_template(recipient, template.wa_template_name, params)
        else:
            # Not approved yet -> try plain text (works inside Meta's 24h window)
            success, detail = whatsapp.send_text(recipient, body)

    elif template.channel == Template.EMAIL:
        recipient = to_email or user.email
        success, detail = email.send_email(recipient, render(template.subject, context), body)

    else:  # Web Push
        recipient = f"user #{user.id}"
        success, detail = webpush.send_push(user.id, render(template.title, context), body)

    message_id = MESSAGE_ID.search(detail) if template.channel == Template.WHATSAPP else None
    NotificationLog.objects.create(
        trigger=template.trigger, channel=template.channel, user=user,
        recipient=recipient, success=success, is_test=is_test, response=detail,
        message_id=message_id.group(1) if message_id else "",
    )
    return success, detail


def fire_trigger(trigger_key, user):
    """Send every enabled template of this trigger to the user."""
    templates = Template.objects.filter(trigger__key=trigger_key, enabled=True).select_related("trigger")
    results = []
    for template in templates:
        try:
            results.append((template.channel, *send_one(template, user)))
        except Exception as error:  # one channel failing must not stop the others
            NotificationLog.objects.create(
                trigger=template.trigger, channel=template.channel, user=user, success=False, response=str(error)
            )
            results.append((template.channel, False, str(error)))
    return results


def fire_trigger_in_background(trigger_key, user):
    """Don't make the user wait for 3 API calls while logging in."""

    def run():
        try:
            fire_trigger(trigger_key, user)
        finally:
            connection.close()  # each thread gets its own DB connection

    threading.Thread(target=run, daemon=True).start()


# ---------- WhatsApp template approval ----------

def to_numbered(body):
    """'Hi {{name}}, {{email}}' -> ('Hi {{1}}, {{2}}', ['name', 'email'])  (the variable mapping)"""
    names = []

    def replace(match):
        if match.group(1) not in names:
            names.append(match.group(1))
        return "{{%d}}" % (names.index(match.group(1)) + 1)

    return VARIABLE.sub(replace, body), names


def sync_whatsapp_template(template):
    """First call submits the template to Meta, later calls refresh its approval status."""
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_BUSINESS_ACCOUNT_ID:
        return False, "WHATSAPP_ACCESS_TOKEN / WHATSAPP_BUSINESS_ACCOUNT_ID not set in .env"

    if not template.wa_template_id:
        body, names = to_numbered(template.body)
        template.wa_version += 1
        name = f"{template.trigger.key}_{template.id}_v{template.wa_version}".replace("-", "_").lower()
        ok, data = whatsapp.create_template(name, body, [VARIABLES.get(n, "test") for n in names])
        if not ok and (existing := whatsapp.find_template(name)):
            # Same name already submitted (e.g. by the local copy of this app) -> reuse it
            ok, data = True, existing
        if not ok:
            template.save(update_fields=["wa_version"])
            error = data.get("error", {})
            return False, error.get("error_user_msg") or error.get("message") or str(data)
        template.wa_template_id = data["id"]
        template.wa_template_name = name
        template.wa_status = data.get("status", "PENDING")
        template.wa_variables = names
    else:
        ok, data = whatsapp.get_template_status(template.wa_template_id)
        if not ok:
            return False, data.get("error", {}).get("message") or str(data)
        template.wa_status = data.get("status", template.wa_status)

    template.save()
    return True, template.wa_status


def save_whatsapp_statuses(payload):
    """Webhook from Meta: update the log rows with sent / delivered / read / failed (+ reason)."""
    updated = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for status in change.get("value", {}).get("statuses", []):
                if not status.get("id"):
                    continue
                text = status.get("status", "")
                errors = status.get("errors") or []
                if errors:
                    error = errors[0]
                    reason = error.get("error_data", {}).get("details") or error.get("message") or error.get("title", "")
                    text = f"failed: {error.get('code')} {reason}"
                WhatsAppStatus.objects.create(
                    message_id=status["id"], status=status.get("status", ""),
                    error=text[len("failed: "):][:500] if errors else "",
                )
                fields = {"delivery_status": text[:255]}
                if errors:
                    fields["success"] = False
                updated += NotificationLog.objects.filter(message_id=status.get("id")).update(**fields)
    return updated


# ---------- "Not logged in for X" triggers ----------

def check_inactive_users():
    """Run every hour or so (cron / admin button). Fires each inactive trigger once per absence."""
    now = timezone.now()
    rules = [
        ("inactive_1_week", timedelta(days=7), "inactive_week_sent"),
        ("inactive_1_day", timedelta(days=1), "inactive_day_sent"),
    ]
    count = 0
    for trigger_key, gap, flag in rules:
        users = User.objects.filter(profile__last_seen__lte=now - gap, **{f"profile__{flag}": False})
        for user in users:
            fire_trigger(trigger_key, user)
            setattr(user.profile, flag, True)
            if flag == "inactive_week_sent":
                user.profile.inactive_day_sent = True  # don't also send "1 day" after "1 week"
            user.profile.save()
            count += 1
    return count
