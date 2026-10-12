"""WhatsApp texts that Meta refused.

- A variable can't be the last thing in the message.
- Texts about logging in / passwords are treated by Meta as "authentication" (one-time codes only),
  so login and reset messages avoid that wording.
"""

from django.db import migrations

# trigger: (old text, new text)
FIXES = {
    "login": (
        "Hi {{name}}, welcome back to {{site_name}}! You logged in at {{time}}.",
        "Hi {{name}}, welcome back to {{site_name}}! Great to see you again, enjoy your visit.",
    ),
    "inactive_1_week": (
        "Hi {{name}}, we miss you, come back to {{site_name}}!",
        "Hi {{name}}, it's been a week. We miss you at {{site_name}}, come back soon!",
    ),
    "password_reset": (
        "Hi {{name}}, a password reset was requested for your {{site_name}} account.",
        "Hi {{name}}, we received your request on {{site_name}}. Please check your email inbox for the next steps.",
    ),
}


def fix(apps, schema_editor):
    Template = apps.get_model("notifications", "Template")
    for key, (old, new) in FIXES.items():
        # Only touch texts the admin hasn't changed; reset so Sync submits the new text
        Template.objects.filter(trigger__key=key, channel="whatsapp", body=old).update(
            body=new, wa_template_id="", wa_status="DRAFT"
        )


class Migration(migrations.Migration):
    dependencies = [("notifications", "0003_more_templates")]
    operations = [migrations.RunPython(fix, migrations.RunPython.noop)]
