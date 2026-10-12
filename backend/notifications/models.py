from django.conf import settings
from django.db import models


class Trigger(models.Model):
    """One row in the admin table, e.g. "login" or "order_placed"."""

    key = models.SlugField(unique=True, help_text="Used in code, e.g. login")
    name = models.CharField(max_length=100, help_text="Shown in admin, e.g. Login")
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Template(models.Model):
    """One cell in the admin table: the message for one trigger on one channel."""

    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEBPUSH = "webpush"
    CHANNELS = [(WHATSAPP, "WhatsApp"), (EMAIL, "Email"), (WEBPUSH, "Web Push")]

    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name="templates")
    channel = models.CharField(max_length=20, choices=CHANNELS)
    enabled = models.BooleanField(default=True)

    # Email uses subject, Web Push uses title. Body is used by all channels.
    # Write variables like {{name}} — see services.build_context for the list.
    subject = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    # WhatsApp only: Meta must approve a template before we can send it.
    wa_template_name = models.CharField(max_length=100, blank=True)
    wa_template_id = models.CharField(max_length=100, blank=True)
    wa_status = models.CharField(max_length=30, default="DRAFT")  # DRAFT / PENDING / APPROVED / REJECTED
    wa_version = models.PositiveIntegerField(default=0)
    # Variable mapping: WhatsApp wants {{1}}, {{2}}... so we remember which name is which number.
    wa_variables = models.JSONField(default=list, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["trigger", "channel"]

    def __str__(self):
        return f"{self.trigger.key} / {self.channel}"


class NotificationLog(models.Model):
    """Every send attempt, so the admin can see what worked and what failed."""

    trigger = models.ForeignKey(Trigger, on_delete=models.SET_NULL, null=True)
    channel = models.CharField(max_length=20)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    recipient = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=False)
    is_test = models.BooleanField(default=False)
    response = models.TextField(blank=True)
    # WhatsApp only: Meta's message id, and what its webhook later told us (sent / delivered / read / failed)
    message_id = models.CharField(max_length=200, blank=True, db_index=True)
    delivery_status = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
