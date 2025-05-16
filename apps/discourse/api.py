# apps/discourse/api.py
import hmac
import hashlib
import logging

# import base64
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from .sso import generate_sso_payload

logger = logging.getLogger(__name__)
User = get_user_model()

DISCOURSE_API_URL = f"{settings.DISCOURSE_INSTANCE_URL}/users"
DISCOURSE_API_KEY = settings.DISCOURSE_API_KEY
DISCOURSE_ADMIN_USERNAME = settings.DISCOURSE_ADMIN_USERNAME
DISCOURSE_CONNECT_SECRET = settings.DISCOURSE_CONNECT_SECRET  # Shared secret


def generate_signature(sso_payload):
    """
    Generate an HMAC-SHA256 signature for the given payload.
    """
    return hmac.new(
        settings.DISCOURSE_CONNECT_SECRET.encode(), sso_payload.encode(), hashlib.sha256
    ).hexdigest()


# def generate_sso_payload(user, nonce, return_url):
#    """Generate the SSO payload for Discourse."""
#    payload = f"nonce={nonce}&email={user.email}&external_id={user.id}&username={user.username}"
#    encoded_payload = base64.b64encode(payload.encode()).decode()
#    sig = hmac.new(DISCOURSE_CONNECT_SECRET.encode(), encoded_payload.encode(),
#    hashlib.sha256).hexdigest()
#    return encoded_payload, sig


def sync_user_with_discourse(user):
    """Sync a Django user with Discourse (Create or Update)."""

    # Step 1: Skip superuser accounts
    if user.is_superuser:
        logger.info(f"Skipping sync for Django superuser: %s", user.username)
        return

    nonce = "sync_nonce"
    return_url = settings.DISCOURSE_SSO_RETURN_URL

    sso_payload, sig = generate_sso_payload(user, nonce, return_url)

    data = {"sso": sso_payload, "sig": sig}

    headers = {
        "Api-Key": DISCOURSE_API_KEY,
        "Api-Username": DISCOURSE_ADMIN_USERNAME,
        "Content-Type": "application/json",
    }

    sync_url = f"{settings.DISCOURSE_INSTANCE_URL}/admin/users/sync_sso"

    try:
        response = requests.post(
            sync_url, json=data, headers=headers, verify=False, timeout=10
        )
        response.raise_for_status()
        logger.info(f"User %s synchronized with Discourse successfully.", user.username)
    except requests.RequestException as e:
        logger.error(f"Failed to sync user %s with Discourse: %s", user.username, e)


def fetch_discourse_data(endpoint, params=None):
    """
    Generic function to fetch data from a specified Discourse API endpoint.
    """
    try:
        url = f"{settings.DISCOURSE_INSTANCE_URL}/{endpoint}"
        headers = {
            "Api-Key": settings.DISCOURSE_API_KEY,
            "Api-Username": "system",
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Error fetching data from Discourse endpoint %s: %s", endpoint, e)
        raise Exception("Error fetching data from Discourse") from e
