# apps/discourse/sso.py

import base64
import hmac
import hashlib
import urllib.parse
import logging
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .exceptions import SSOValidationError

logger = logging.getLogger(__name__)

def decode_sso_payload(sso):
    """
    Decode the Base64-encoded SSO payload and return parameters as a dict.
    Raises SSOValidationError if decoding fails.
    """
    try:
        decoded = base64.b64decode(sso).decode()
        return dict(urllib.parse.parse_qsl(decoded))
    except Exception as e:
        raise SSOValidationError("Invalid payload encoding") from e

def verify_signature(sso, sig):
    """
    Verify that the provided HMAC-SHA256 signature matches the expected signature.
    Raises SSOValidationError if the signature is invalid.
    """
    expected_sig = hmac.new(
        settings.DISCOURSE_CONNECT_SECRET.encode(),
        sso.encode(),
        hashlib.sha256
    ).hexdigest()

     # Log comparison for debugging
    logger.debug(f"Expected Signature: {expected_sig}")
    logger.debug(f"Provided Signature: {sig}")

    if expected_sig != sig:
        logger.error(f"Expected Signature: {expected_sig}, Provided Signature: {sig}")
        raise SSOValidationError("Invalid signature")

    if not hmac.compare_digest(expected_sig, sig):
        raise SSOValidationError("Invalid signature")

def generate_sso_payload(user, nonce, return_url):
    """
    Generate a new Base64-encoded payload with the user’s details.
    """
    payload = {
        'nonce': nonce,
        'email': user.email,
        'external_id': str(user.id),
        'username': user.username,
        'name': f"{user.first_name} {user.last_name}".strip(),
    }
    query_string = urllib.parse.urlencode(payload)
    return base64.b64encode(query_string.encode()).decode()

def build_redirect_url(return_url, sso_payload):
    """
    Build the redirect URL by appending sso_payload and its signature as query parameters.
    """
    sig = hmac.new(
        settings.DISCOURSE_CONNECT_SECRET.encode(),
        sso_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{return_url}?sso={urllib.parse.quote(sso_payload)}&sig={sig}"

def validate_return_url(url):
    """
    Validate that the return_sso_url in the payload is a properly formatted URL.
    Raises SSOValidationError if validation fails.
    """
    logger.debug(f"Validating return URL: {url}")  # Log the URL being processed
 
    validator = URLValidator(schemes=["http", "https"])
    try:
        validator(url)
    except ValidationError:
        raise SSOValidationError("Invalid return_sso_url")
    
    return url
        
def error_response(message, status=400):
    """
    Centralized function to generate an error response.
    Here we simply return an HttpResponseBadRequest, but you could
    expand this to return a JsonResponse if using an API.
    """
    from django.http import HttpResponseBadRequest
    return HttpResponseBadRequest(message)

