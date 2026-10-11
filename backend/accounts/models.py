from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """Extra info we need to reach a user on every channel."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, help_text="WhatsApp number with country code, e.g. 919876543210")
    last_seen = models.DateTimeField(null=True, blank=True)

    # So the "not logged in" triggers fire only once per absence
    inactive_day_sent = models.BooleanField(default=False)
    inactive_week_sent = models.BooleanField(default=False)

    def mark_seen(self):
        """User is active right now -> restart the "not logged in for X" countdown."""
        self.last_seen = timezone.now()
        self.inactive_day_sent = False
        self.inactive_week_sent = False
        self.save()

    def __str__(self):
        return self.user.email
