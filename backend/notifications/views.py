import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from . import services
from .models import NotificationLog, Template, Trigger
from .serializers import NotificationLogSerializer, TemplateSerializer, TriggerSerializer


# ---------- Admin: Notification Settings ----------

class TriggerViewSet(viewsets.ModelViewSet):
    """Rows of the admin table."""

    queryset = Trigger.objects.prefetch_related("templates")
    serializer_class = TriggerSerializer
    permission_classes = [IsAdminUser]


class TemplateViewSet(viewsets.ModelViewSet):
    """Cells of the admin table: create / edit / on-off (PATCH enabled) / test / sync."""

    queryset = Template.objects.select_related("trigger")
    serializer_class = TemplateSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Send this template to the admin (or to the phone / email given in the request)."""
        success, detail = services.send_one(
            self.get_object(), request.user, is_test=True,
            phone=request.data.get("phone"), to_email=request.data.get("email"),
        )
        return Response({"success": success, "detail": detail}, status=200 if success else 400)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """WhatsApp only: submit to Meta, then press again until APPROVED."""
        template = self.get_object()
        if template.channel != Template.WHATSAPP:
            return Response({"detail": "Only WhatsApp templates need syncing"}, status=400)
        success, detail = services.sync_whatsapp_template(template)
        return Response(
            {"success": success, "detail": detail, "template": TemplateSerializer(template).data},
            status=200 if success else 400,
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def logs(request):
    return Response(NotificationLogSerializer(NotificationLog.objects.select_related("trigger", "user")[:50], many=True).data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def variables(request):
    return Response(services.VARIABLES)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def run_inactivity_check(request):
    return Response({"notified": services.check_inactive_users()})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def cron_inactivity_check(request):
    """Called every hour by .github/workflows/inactivity-check.yml with the shared CRON_SECRET."""
    if not settings.CRON_SECRET or request.headers.get("X-Cron-Secret") != settings.CRON_SECRET:
        return Response({"error": "Wrong or missing X-Cron-Secret"}, status=403)
    return Response({"notified": services.check_inactive_users()})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def status(request):
    """Public health check: which providers are configured (yes/no only, never the keys)."""
    from django.contrib.auth.models import User

    return Response({
        "email_resend": bool(settings.RESEND_API_KEY),
        "email_from": settings.RESEND_FROM_EMAIL,
        "webpush_onesignal": bool(settings.ONESIGNAL_APP_ID and settings.ONESIGNAL_REST_API_KEY),
        "whatsapp": bool(settings.WHATSAPP_ACCESS_TOKEN and settings.PHONE_NUMBER_ID),
        "whatsapp_webhook": bool(settings.WHATSAPP_VERIFY_TOKEN),
        "admin_exists": User.objects.filter(is_staff=True).exists(),
        "triggers": Trigger.objects.count(),
        "enabled_templates": Template.objects.filter(enabled=True).count(),
        "cors_allowed_origins": settings.CORS_ALLOWED_ORIGINS,
    })


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    """Meta calls this. GET = one-time check when you save the webhook, POST = message status updates."""
    if request.method == "GET":
        if (
            settings.WHATSAPP_VERIFY_TOKEN
            and request.GET.get("hub.mode") == "subscribe"
            and request.GET.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN
        ):
            return HttpResponse(request.GET.get("hub.challenge", ""))  # Meta wants it back as plain text
        return HttpResponse("Verify token mismatch", status=403)

    # If WHATSAPP_APP_SECRET is set, only accept requests really signed by Meta
    if settings.WHATSAPP_APP_SECRET:
        expected = "sha256=" + hmac.new(
            settings.WHATSAPP_APP_SECRET.encode(), request.body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, request.headers.get("X-Hub-Signature-256", "")):
            return HttpResponse("Bad signature", status=403)

    services.save_whatsapp_statuses(json.loads(request.body or b"{}"))
    return HttpResponse("ok")  # always 200 quickly, or Meta keeps retrying


# ---------- Website: fire any trigger (e.g. "order_placed") ----------

@api_view(["POST"])
def fire_event(request):
    key = request.data.get("trigger", "")
    if not Trigger.objects.filter(key=key).exists():
        return Response({"error": f"Unknown trigger '{key}'"}, status=400)
    request.user.profile.mark_seen()
    services.fire_trigger_in_background(key, request.user)
    return Response({"ok": True})
