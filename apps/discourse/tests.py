# apps/discourse/tests.py
import base64
import hashlib
import hmac
import urllib.parse
import logging
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.discourse.models import DiscourseProfile, SsoEventLog
from apps.discourse.api import sync_user_with_discourse, fetch_discourse_data
from apps.discourse.exceptions import SSOValidationError

logger = logging.getLogger(__name__)
User = get_user_model()

@override_settings(
    DISCOURSE_CONNECT_SECRET="<secret>",
    DISCOURSE_SSO_RETURN_URL="<url>"
)
# ----------------------------
# Model Tests
# ----------------------------
class DiscourseModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='secret', email='test@example.com')

    def test_discourse_profile_auto_created(self):
        profile = DiscourseProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile)
        self.assertEqual(str(profile), f"DiscourseProfile for {self.user}")

    def test_sso_event_log_str(self):
        event = SsoEventLog.objects.create(user=self.user, event_type='login', payload_details='Test payload', signature='abcdef')
        self.assertIn("SSO Event: login", str(event))

# ----------------------------
# SSO Views Tests
# ----------------------------

class DiscourseSSOViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sso_user', password='secret', email='sso@example.com')
        self.client.login(username='sso_user', password='secret')

    def build_sso_payload(self, nonce='123456', return_url='http://dummy.com'):
        query_string = urllib.parse.urlencode({'nonce': nonce, 'return_sso_url': return_url})
        sso_payload = base64.b64encode(query_string.encode()).decode()
        sig = hmac.new(settings.DISCOURSE_CONNECT_SECRET.encode(), sso_payload.encode(), hashlib.sha256).hexdigest()
        return sso_payload, sig

    def test_sso_provider_missing_params(self):
        url = reverse('discourse:discourse_sso_provider')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_sso_provider_invalid_signature(self):
        sso_payload, sig = self.build_sso_payload()
        #bad_sig = "invalid" + sig[7:]  # Simulated incorrect signature
        bad_sig = "bad_signature"  # Simulated incorrect signature

        logger.debug(f"Generated valid signature for test: {sig}")
        logger.debug(f"Using bad signature: {bad_sig}")

        url = reverse('discourse:discourse_sso_provider')
        response = self.client.get(url, data={'sso': sso_payload, 'sig': bad_sig})

        self.assertEqual(response.status_code, 400)

    def test_sso_provider_valid_payload(self):
        sso_payload, sig = self.build_sso_payload()
        url = reverse('discourse:discourse_sso_provider')
        response = self.client.get(url, data={'sso': sso_payload, 'sig': sig})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("http://dummy.com"))

# ----------------------------
# API Client Module Tests
# ----------------------------
class DiscourseAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='secret', email='api@example.com')

    @patch('apps.discourse.api.requests.post')
    def test_sync_user_with_discourse_success(self, mock_post):
        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {'success': True}
        fake_response.raise_for_status.return_value = None
        mock_post.return_value = fake_response

        result = sync_user_with_discourse(self.user)
        self.assertEqual(result, {'success': True})
        mock_post.assert_called_once()

    @patch('apps.discourse.api.requests.get')
    def test_fetch_discourse_data_failure(self, mock_get):
        fake_response = MagicMock()
        fake_response.raise_for_status.side_effect = Exception("Error")
        mock_get.return_value = fake_response

        with self.assertRaises(Exception):
            fetch_discourse_data('some-endpoint')

# ----------------------------
# (Optional) Context Processor Test
# ----------------------------
from apps.discourse.context_processors import discourse_forum_url

class ContextProcessorTestCase(TestCase):
    def test_discourse_forum_url(self):
        fake_request = None  # You might use RequestFactory if needed.
        context = discourse_forum_url(fake_request)
        self.assertIn('forum_url', context)
        self.assertEqual(context['forum_url'], settings.DISCOURSE_INSTANCE_URL)

