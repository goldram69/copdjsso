# apps/discourse/views.py

import logging
import base64
import hmac
import hashlib
import urllib.parse


from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from .exceptions import SSOValidationError
from .mixins import BaseSSOViewMixin
from .sso import error_response
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView

logger = logging.getLogger(__name__)
DISCOURSE_CONNECT_SECRET = settings.DISCOURSE_CONNECT_SECRET  # Same shared secret

def sync_discourse_user(sso, sig):
    """Synchronize user session with Discourse after login"""
    try:
        sync_url = f"{settings.DISCOURSE_INSTANCE_URL}/admin/users/sync_sso"
        sync_data = {"sso": sso, "sig": sig}
        headers = {
            "Content-Type": "application/json",
            "Api-Key": settings.DISCOURSE_API_KEY,
            "Api-Username": settings.DISCOURSE_ADMIN_USERNAME,
        }

        response = requests.post(sync_url, json=sync_data, headers=headers)
        response.raise_for_status()  # Ensure HTTP errors raise exceptions
    except requests.exceptions.RequestException as e:
        logger.error("Failed to sync user with Discourse: %s", e)

def index(request):
 return HttpResponse("Discourse app home. Please use the proper SSO URLs.")


def fix_base64_padding(encoded_str):
    """Fix Base64 encoding issues due to missing padding"""
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += "=" * (4 - missing_padding)  # 🔹 Add missing '=' padding
    return encoded_str

@method_decorator(login_required, name='dispatch')
class DiscourseSSOProviderView(BaseSSOViewMixin, View):
    """
    Handles the Discourse SSO handshake via a GET request.
    Utilizes the BaseSSOViewMixin to perform payload validation and redirection.
    """
    def get(self, request):
        sso = request.GET.get('sso')
        sig = request.GET.get('sig')
        logger.debug(f"Incoming GET parameters: {request.GET}")

        if not sso or not sig:
            logger.error("Missing SSO parameters in request: %s", request.GET)
            return HttpResponseBadRequest("SSO parameters are required.")

        fixed_sso = fix_base64_padding(sso)
        try:
            decoded_payload = base64.b64decode(fixed_sso).decode("utf-8")
        except UnicodeDecodeError:
            logger.error(f"Failed UTF-8 decoding. Raw decoded payload: {base64.b64decode(fixed_sso)}")
            return HttpResponseBadRequest("SSO payload decoding failed.")

        logger.debug(f"Decoded SSO payload: {decoded_payload}")
        params = dict(item.split("=") for item in decoded_payload.split("&") if "=" in item)
        nonce = params.get("nonce")
        return_sso_url = params.get("return_sso_url")
        if not nonce or not return_sso_url:
            logger.error("SSO payload missing required nonce or return_sso_url")
            return HttpResponseBadRequest("Invalid SSO payload.")

        # If user is not authenticated, redirect them to login
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?sso={sso}&sig={sig}")

        # Now that the user is authenticated, generate a return payload.
        try:
            # This function should build a query string that includes external_id, email, username, etc.
            response_payload = generate_sso_payload(request.user, nonce, return_sso_url)
            redirect_url = build_redirect_url(return_sso_url, response_payload)
            return HttpResponseRedirect(redirect_url)
        except Exception as e:
            logger.error("Error generating SSO response: %s", e)
            return HttpResponseBadRequest("Error generating SSO response.")

    def post(self, request):
     sso = request.POST.get('sso')
     sig = request.POST.get('sig')
    
     if not sso or not sig:
        logger.error("Missing SSO parameters in POST request.")
        return HttpResponseBadRequest("Missing SSO parameters.")

     try:
        verify_signature(sso, sig)
        payload = decode_sso_payload(sso)
     except Exception as e:
        logger.error("Error verifying SSO payload in POST: %s", e)
        return HttpResponseBadRequest("Invalid payload or signature.")

     nonce = payload.get("nonce")
     return_sso_url = payload.get("return_sso_url")
     external_id = payload.get("external_id")  # Ensure external_id is provided

     if not nonce or not return_sso_url or not external_id:
        logger.error("Missing required parameters in payload (POST).")
        return HttpResponseBadRequest("Missing required parameters in payload.")

    # Authenticate user in Django using external_id
     User = get_user_model()
     try:
        user = User.objects.get(id=external_id)
        login(request, user)  # Log in user in Django session
     except User.DoesNotExist:
        logger.error("SSO login failed: User not found in Django.")
        return HttpResponseBadRequest("User not found.")

     try:
        response_payload = generate_sso_payload(user, nonce, return_sso_url)
        redirect_url = build_redirect_url(return_sso_url, response_payload)
     except Exception as e:
        logger.error("Error generating SSO response in POST: %s", e)
        return HttpResponseBadRequest("Error generating SSO response.")

     logger.info("SSO login processed successfully for user %s", user.id)
     return redirect(redirect_url) 

# Import helper functions from your SSO module
from .sso import decode_sso_payload, verify_signature, generate_sso_payload, build_redirect_url


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class DiscourseSSOLoginView(View):
    """
    POST endpoint for handling the SSO callback from Discourse.

    This view is CSRF exempt because the POST request is coming from a non-browser
    source (Discourse) and relies on HMAC verification. It requires an authenticated user.
    """
    def post(self, request):
        sso = request.POST.get('sso')
        sig = request.POST.get('sig')
        if not sso or not sig:
            logger.error("Missing SSO parameters in POST request.")
            return HttpResponseBadRequest("Missing SSO parameters.")

        try:
            verify_signature(sso, sig)
            payload = decode_sso_payload(sso)
        except Exception as e:
            logger.error("Error verifying SSO payload in POST: %s", e)
            return HttpResponseBadRequest("Invalid payload or signature.")

        nonce = payload.get("nonce")
        return_sso_url = payload.get("return_sso_url")
        if not nonce or not return_sso_url:
            logger.error("Missing required parameters in payload (POST).")
            return HttpResponseBadRequest("Missing required parameters in payload.")

        try:
            response_payload = generate_sso_payload(request.user, nonce, return_sso_url)
            redirect_url = build_redirect_url(return_sso_url, response_payload)
        except Exception as e:
            logger.error("Error generating SSO response in POST: %s", e)
            return HttpResponseBadRequest("Error generating SSO response.")

        logger.info("SSO login processed successfully for user %s", request.user.id)
        return redirect(redirect_url)



def discourse_sso_provider(request):
    """Handles Discourse SSO login requests."""
    sso_payload = request.GET.get('sso')
    sig = request.GET.get('sig')

    # Verify signature
    expected_sig = hmac.new(DISCOURSE_SSO_SECRET.encode(), sso_payload.encode(), hashlib.sha256).hexdigest()
    if expected_sig != sig:
        return HttpResponseBadRequest("Invalid SSO request.")

    # Decode payload
    decoded_payload = base64.b64decode(sso_payload).decode()
    params = dict(item.split('=') for item in decoded_payload.split('&'))
    external_id = params.get("external_id")

    # Authenticate user in Django
    User = get_user_model()
    try:
        user = User.objects.get(id=external_id)
        login(request, user)
        return HttpResponseRedirect(settings.DISCOURSE_SSO_RETURN_URL)
    except User.DoesNotExist:
        return HttpResponseBadRequest("User not found.")

class CustomLoginView(LoginView):
    """Preserve SSO parameters when redirecting after login"""
    def get_success_url(self):
        next_url = self.request.GET.get("next", "/")
        sso = self.request.GET.get("sso", "")
        sig = self.request.GET.get("sig", "")

        # Ensure we only redirect when valid SSO parameters are present
        if sso and sig:
            return f"/discourse/session/sso_provider/?sso={sso}&sig={sig}"
        return next_url
