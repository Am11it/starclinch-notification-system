from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from notifications.services import fire_trigger_in_background

from .models import Profile
from .serializers import UserSerializer


def login_response(user):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400)
    if User.objects.filter(username=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    user = User.objects.create_user(
        username=email, email=email, password=password, first_name=request.data.get("name", "")
    )
    Profile.objects.create(user=user, phone=request.data.get("phone", ""), last_seen=timezone.now())
    fire_trigger_in_background("signup", user)
    return login_response(user)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email", "").strip().lower()
    user = authenticate(username=email, password=request.data.get("password", ""))
    if not user:
        return Response({"error": "Wrong email or password"}, status=400)

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.mark_seen()

    fire_trigger_in_background("login", user)
    return login_response(user)


@api_view(["POST"])
def logout(request):
    fire_trigger_in_background("logout", request.user)
    Token.objects.filter(user=request.user).delete()
    return Response({"ok": True})


@api_view(["GET", "PATCH"])
def me(request):
    # The website calls this on every page load, so it doubles as "user visited"
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.mark_seen()
    if request.method == "PATCH":
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    """Demo only: we don't really reset anything, we just fire the trigger."""
    email = request.data.get("email", "").strip().lower()
    user = User.objects.filter(username=email).first()
    if user:
        fire_trigger_in_background("password_reset", user)
    # Same answer either way so nobody can guess which emails exist
    return Response({"ok": True, "message": "If that email exists, a reset message was sent."})
