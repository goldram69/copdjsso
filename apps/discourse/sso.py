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
from django.http import HttpResponseBadRequest

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
    logger.debug(f"Expected Signature:  %s", expected_sig)
    logger.debug(f"Provided Signature: %s", sig)

    if expected_sig != sig:
        logger.error(f"Expected Signature: %s, Provided Signature: %s", expected_sig, sig)
        raise SSOValidationError("Invalid signature")

    if not hmac.compare_digest(expected_sig, sig):
        raise SSOValidationError("Invalid signature")

def generate_sso_payload(user, nonce, return_url):
    # Build a dictionary with the user data
    payload_dict = {
        "nonce": nonce,
        "external_id": str(user.id),
        "email": user.email,
        "username": user.username,
        # Add any additional fields as required, for example:
        # "name": user.get_full_name(),
        'name': f"{user.first_name} {user.last_name}".strip(),
    }
    #query_string = urllib.parse.urlencode(payload)
    #return base64.b64encode(query_string.encode()).decode()
    # Convert the dictionary into a URL-encoded query string
    payload = urllib.parse.urlencode(payload_dict)
    # Base64 encode the payload
    b64_payload = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
    # Generate a signature using your shared secret
    sig = hmac.new(
        settings.DISCOURSE_CONNECT_SECRET.encode('utf-8'),
        b64_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Return a payload in the form "sso=…&sig=…"
    return f"sso={urllib.parse.quote(b64_payload)}&sig={sig}"

def build_redirect_url(return_sso_url, payload):
    # Make sure return_sso_url is absolute
    parsed = urllib.parse.urlparse(return_sso_url)
    if parsed.scheme not in ['http', 'https']:
        # Fallback if non-absolute; normally, this should not happen.
        return f"{return_sso_url}?{payload}"
    
    # Append (or merge) the payload with any existent query parameters.
    if parsed.query:
        new_query = parsed.query + "&" + payload
    else:
        new_query = payload
    return parsed._replace(query=new_query).geturl()

def fix_base64_padding(encoded_str):
    """Add missing padding to a Base64 string if necessary."""
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += "=" * (4 - missing_padding)
    return encoded_str

def validate_return_url(url):
    """
    Validate that the return_sso_url in the payload is a properly formatted URL.
    Raises SSOValidationError if validation fails.
    """
    logger.debug(f"Validating return URL: %s", url)  # Log the URL being processed
 
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
    return HttpResponseBadRequest(message)

