"""Creates the default trigger rows, plus starter templates for Login and Logout."""

from django.db import migrations

TRIGGERS = [
    ("login", "Login", "User signs in on the website"),
    ("logout", "Logout", "User signs out"),
    ("signup", "Sign up", "User creates an account"),
    ("inactive_1_day", "Not logged in for 1 day", "User has not visited for 24 hours"),
    ("inactive_1_week", "Not logged in for 1 week", "User has not visited for 7 days"),
    ("password_reset", "Password reset", "User asks to reset password"),
    ("order_placed", "Order placed", "User completes a purchase"),
]

# (trigger, channel, subject, title, body)
TEMPLATES = [
    ("login", "whatsapp", "", "", "Hi {{name}}, welcome back to {{site_name}}! You logged in at {{time}}."),
    ("login", "email", "You logged in successfully", "", "Hi {{name}},\n\nYou logged in to {{site_name}} at {{time}}.\n\nIf this wasn't you, please reset your password."),
    ("login", "webpush", "", "Welcome back, {{name}}!", "Good to see you again on {{site_name}}."),
    ("logout", "whatsapp", "", "", "Bye {{name}}, you have logged out of {{site_name}}. See you soon!"),
    ("logout", "email", "You have logged out", "", "Hi {{name}},\n\nYou logged out of {{site_name}} at {{time}}. Come back soon!"),
    ("logout", "webpush", "", "See you soon, {{name}}", "You have logged out of {{site_name}}."),
]


def seed(apps, schema_editor):
    Trigger = apps.get_model("notifications", "Trigger")
    Template = apps.get_model("notifications", "Template")
    for key, name, description in TRIGGERS:
        Trigger.objects.get_or_create(key=key, defaults={"name": name, "description": description})
    for key, channel, subject, title, body in TEMPLATES:
        Template.objects.get_or_create(
            trigger=Trigger.objects.get(key=key), channel=channel,
            defaults={"subject": subject, "title": title, "body": body},
        )


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
