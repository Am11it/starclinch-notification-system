"""Browser push via OneSignal. Docs: https://documentation.onesignal.com/reference/push-notification

The frontend calls OneSignal.login(<our user id>), so here we can target a user
by that "external_id" without storing any subscription ids ourselves.
"""

import requests
from django.conf import settings

from . import to_result


def send_push(user_id, title, body):
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_REST_API_KEY:
        return False, "ONESIGNAL_APP_ID / ONESIGNAL_REST_API_KEY not set in .env"

    key = settings.ONESIGNAL_REST_API_KEY
    # New OneSignal keys start with "os_v2_" and use "Key", older ones use "Basic"
    auth = f"Key {key}" if key.startswith("os_v2_") else f"Basic {key}"

    response = requests.post(
        "https://api.onesignal.com/notifications",
        headers={"Authorization": auth, "Content-Type": "application/json"},
        json={
            "app_id": settings.ONESIGNAL_APP_ID,
            "target_channel": "push",
            "include_aliases": {"external_id": [str(user_id)]},
            "headings": {"en": title},
            "contents": {"en": body},
            # Web push only — no iOS / Android
            "isAnyWeb": True,
            "isIos": False,
            "isAndroid": False,
        },
        timeout=15,
    )
    ok, detail = to_result(response)
    # OneSignal answers 200 even when nobody matched, with an "errors" field
    if ok and '"errors"' in response.text:
        return False, detail + " (is this browser subscribed? click 'Enable push' on the website)"
    return ok, detail
