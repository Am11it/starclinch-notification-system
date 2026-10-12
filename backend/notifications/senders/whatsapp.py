"""WhatsApp Cloud API (Meta). Docs: https://developers.facebook.com/docs/whatsapp/cloud-api"""

import requests
from django.conf import settings

from . import to_result

GRAPH_URL = "https://graph.facebook.com/v25.0"
LANGUAGE = "en_US"


def _headers():
    return {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}


def _missing_keys():
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.PHONE_NUMBER_ID:
        return "WHATSAPP_ACCESS_TOKEN / PHONE_NUMBER_ID not set in .env"
    return None


def normalize_phone(phone):
    """'+91 93156-05758' -> '919315605758', '9315605758' -> '919315605758'"""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        digits = settings.DEFAULT_COUNTRY_CODE + digits
    return digits


def send_template(phone, template_name, params):
    """Send an approved template. params = values for {{1}}, {{2}}, ... in order."""
    if error := _missing_keys():
        return False, error
    phone = normalize_phone(phone)
    template = {"name": template_name, "language": {"code": LANGUAGE}}
    if params:
        template["components"] = [
            {"type": "body", "parameters": [{"type": "text", "text": str(p)} for p in params]}
        ]
    payload = {"messaging_product": "whatsapp", "to": phone, "type": "template", "template": template}
    response = requests.post(f"{GRAPH_URL}/{settings.PHONE_NUMBER_ID}/messages", json=payload, headers=_headers(), timeout=15)
    return to_result(response)


def send_text(phone, text):
    """Plain text. Meta only delivers this if the user messaged your test number in the last 24h."""
    if error := _missing_keys():
        return False, error
    phone = normalize_phone(phone)
    payload = {"messaging_product": "whatsapp", "to": phone, "type": "text", "text": {"body": text}}
    response = requests.post(f"{GRAPH_URL}/{settings.PHONE_NUMBER_ID}/messages", json=payload, headers=_headers(), timeout=15)
    return to_result(response)


def create_template(name, body, examples):
    """Submit a new template to Meta for approval. body uses {{1}}, {{2}}..."""
    component = {"type": "BODY", "text": body}
    if examples:
        component["example"] = {"body_text": [examples]}
    payload = {"name": name, "language": LANGUAGE, "category": "UTILITY", "components": [component]}
    url = f"{GRAPH_URL}/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    response = requests.post(url, json=payload, headers=_headers(), timeout=15)
    return response.ok, response.json()


def find_template(name):
    """Look up a template we (or another copy of this app) already submitted with this name."""
    url = f"{GRAPH_URL}/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    response = requests.get(url, params={"name": name, "fields": "id,name,status"}, headers=_headers(), timeout=15)
    matches = [t for t in response.json().get("data", []) if t.get("name") == name] if response.ok else []
    return matches[0] if matches else None


def get_template_status(template_id):
    """Ask Meta whether our template is PENDING / APPROVED / REJECTED."""
    response = requests.get(f"{GRAPH_URL}/{template_id}", params={"fields": "name,status"}, headers=_headers(), timeout=15)
    return response.ok, response.json()
