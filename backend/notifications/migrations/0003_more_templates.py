"""Starter templates for the rest of the triggers from the PRD (all 3 channels)."""

from django.db import migrations

# (trigger, channel, subject, title, body)
TEMPLATES = [
    ("signup", "email", "Welcome to {{site_name}}!", "",
     "Hi {{name}},\n\nThanks for creating your {{site_name}} account. We're happy to have you!"),
    ("signup", "whatsapp", "", "", "Hi {{name}}, welcome to {{site_name}}! Your account is ready."),
    ("signup", "webpush", "", "Welcome, {{name}}!", "Your {{site_name}} account is ready."),

    ("inactive_1_day", "email", "We haven't seen you today, {{name}}", "",
     "Hi {{name}},\n\nIt's been a day since your last visit to {{site_name}}. Come back and see what's new!"),
    ("inactive_1_day", "whatsapp", "", "", "Hi {{name}}, we missed you today on {{site_name}}. Come say hi!"),
    ("inactive_1_day", "webpush", "", "Missed you today", "Come back to {{site_name}}, {{name}}!"),

    ("inactive_1_week", "email", "It's been a week...", "",
     "Hi {{name}},\n\nIt's been a week since you visited {{site_name}}. We miss you, come back soon!"),
    ("inactive_1_week", "whatsapp", "", "", "Hi {{name}}, we miss you, come back to {{site_name}}!"),
    ("inactive_1_week", "webpush", "", "Come visit us again", "It's been a week, {{name}}. We miss you!"),

    ("password_reset", "email", "Reset your {{site_name}} password", "",
     "Hi {{name}},\n\nWe got a request to reset your password at {{time}}.\nIf this wasn't you, you can ignore this email."),
    ("password_reset", "whatsapp", "", "", "Hi {{name}}, a password reset was requested for your {{site_name}} account."),
    ("password_reset", "webpush", "", "Password reset requested", "Check your email to reset your password, {{name}}."),

    ("order_placed", "email", "Your order is confirmed", "",
     "Hi {{name}},\n\nThanks for your order on {{site_name}}! It was placed at {{time}}."),
    ("order_placed", "whatsapp", "", "", "Hi {{name}}, thanks for your order on {{site_name}}! It is confirmed."),
    ("order_placed", "webpush", "", "Order confirmed 🎉", "Thanks for your order, {{name}}!"),
]


def seed(apps, schema_editor):
    Trigger = apps.get_model("notifications", "Trigger")
    Template = apps.get_model("notifications", "Template")
    for key, channel, subject, title, body in TEMPLATES:
        trigger = Trigger.objects.filter(key=key).first()
        if trigger:  # admin may have deleted it
            Template.objects.get_or_create(
                trigger=trigger, channel=channel,
                defaults={"subject": subject, "title": title, "body": body},
            )


class Migration(migrations.Migration):
    dependencies = [("notifications", "0002_seed_triggers")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
