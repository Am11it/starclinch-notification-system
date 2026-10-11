from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="profile.phone", allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "phone", "is_staff"]
        read_only_fields = ["id", "email", "is_staff"]

    def update(self, user, data):
        profile_data = data.pop("profile", {})
        user.first_name = data.get("first_name", user.first_name)
        user.save()
        if "phone" in profile_data:
            user.profile.phone = profile_data["phone"]
            user.profile.save()
        return user
