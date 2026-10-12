import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_key(name):
    """Read a provider key; placeholders copied from .env.example (your_...) count as empty."""
    value = os.getenv(name, "").strip()
    return "" if value.startswith("your_") else value


def env_list(name, default=""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):  # set automatically by Render
    ALLOWED_HOSTS.append(os.getenv("RENDER_EXTERNAL_HOSTNAME"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "accounts",
    "notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Frontend talks to us with a token: "Authorization: Token <key>"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# Notification provider keys (see .env.example)
WHATSAPP_ACCESS_TOKEN = env_key("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = env_key("PHONE_NUMBER_ID")
WHATSAPP_BUSINESS_ACCOUNT_ID = env_key("WHATSAPP_BUSINESS_ACCOUNT_ID")
# Webhook: any text you choose (also typed into Meta), and optionally the App Secret to check signatures
WHATSAPP_VERIFY_TOKEN = env_key("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET = env_key("WHATSAPP_APP_SECRET")
RESEND_API_KEY = env_key("RESEND_API_KEY")
RESEND_FROM_EMAIL = env_key("RESEND_FROM_EMAIL") or "onboarding@resend.dev"
ONESIGNAL_APP_ID = env_key("ONESIGNAL_APP_ID")
ONESIGNAL_REST_API_KEY = env_key("ONESIGNAL_REST_API_KEY")

# Shared secret for the hourly "not logged in" check (see .github/workflows)
CRON_SECRET = os.getenv("CRON_SECRET", "")

# Added to 10-digit phone numbers that have no country code (91 = India)
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "91")
