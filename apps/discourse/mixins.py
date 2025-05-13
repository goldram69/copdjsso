# apps/discourse/mixins.py

from .exceptions import SSOValidationError
from .sso import verify_signature, decode_sso_payload, validate_return_url, generate_sso_payload, build_redirect_url

class BaseSSOViewMixin:
    """
    A mixin that encapsulates common logic for SSO views.
    Provides methods to validate and decode the SSO payload and
    to build the redirect URL.
    """
    def validate_and_decode_payload(self, sso, sig):
        # Verify the signature and decode the payload.
        verify_signature(sso, sig)
        payload = decode_sso_payload(sso)
        if 'nonce' not in payload:
            raise SSOValidationError("Missing nonce parameter in payload")
        if 'return_sso_url' not in payload:
            raise SSOValidationError("Missing return_sso_url parameter in payload")
        validate_return_url(payload['return_sso_url'])
        return payload

    def build_response_url(self, user, payload):
        """
        Generate a new SSO payload with the user’s data and build the redirect URL.
        """
        nonce = payload.get('nonce')
        return_url = payload.get('return_sso_url')
        sso_payload = generate_sso_payload(user, nonce, return_url)
        return build_redirect_url(return_url, sso_payload)

