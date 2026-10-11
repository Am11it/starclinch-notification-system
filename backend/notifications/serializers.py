from rest_framework import serializers

from .models import NotificationLog, Template, Trigger


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = [
            "id", "trigger", "channel", "enabled", "subject", "title", "body",
            "wa_template_name", "wa_status", "wa_variables", "updated_at",
        ]
        read_only_fields = ["wa_template_name", "wa_status", "wa_variables"]

    def validate(self, data):
        channel = data.get("channel") or self.instance.channel
        if channel == Template.EMAIL and not (data.get("subject") or getattr(self.instance, "subject", "")):
            raise serializers.ValidationError({"subject": "Email needs a subject"})
        if channel == Template.WEBPUSH and not (data.get("title") or getattr(self.instance, "title", "")):
            raise serializers.ValidationError({"title": "Web Push needs a title"})
        return data

    def update(self, template, data):
        # Changing WhatsApp text means Meta must approve it again -> back to draft
        if template.channel == Template.WHATSAPP and "body" in data and data["body"] != template.body:
            template.wa_template_id = ""
            template.wa_status = "DRAFT"
        return super().update(template, data)


class TriggerSerializer(serializers.ModelSerializer):
    # {"whatsapp": {...} | null, "email": {...} | null, "webpush": {...} | null}
    templates = serializers.SerializerMethodField()

    class Meta:
        model = Trigger
        fields = ["id", "key", "name", "description", "templates"]

    def get_templates(self, trigger):
        by_channel = {t.channel: TemplateSerializer(t).data for t in trigger.templates.all()}
        return {channel: by_channel.get(channel) for channel, _ in Template.CHANNELS}


class NotificationLogSerializer(serializers.ModelSerializer):
    trigger = serializers.CharField(source="trigger.name", default="")
    user = serializers.CharField(source="user.email", default="")

    class Meta:
        model = NotificationLog
        fields = ["id", "trigger", "channel", "user", "recipient", "success", "is_test", "response", "created_at"]
