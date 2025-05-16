from django.conf import settings
from django.db import models


class DiscourseProfile(models.Model):
    """
    Stores extra information about a user related to their Discourse account.
    This model is linked via a OneToOneField with the Django user model.
    It holds the Discourse-specific external identifier, username, email, and
    maintains a record of when the data was last synchronized.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discourse_profile",
        verbose_name="Django User",
    )
    external_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique identifier for the user in Discourse",
    )
    username = models.CharField(
        max_length=150, null=True, blank=True, help_text="Discourse username"
    )
    email = models.EmailField(
        null=True, blank=True, help_text="Email address linked to the Discourse account"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful sync with Discourse",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Record creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Record update timestamp"
    )

    def __str__(self):
        return f"DiscourseProfile for {self.user}"

    class Meta:
        verbose_name = "Discourse Profile"
        verbose_name_plural = "Discourse Profiles"


class SsoEventLog(models.Model):
    """
    Logs events related to Discourse SSO processes. This includes both successful
    logins and synchronization attempts as well as errors. It provides a historical
    record which can be used to troubleshoot issues with SSO payloads and signature verification.
    """

    EVENT_TYPE_CHOICES = [
        ("login", "Login"),
        ("sync", "Sync"),
        ("error", "Error"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Associated Django user (if applicable)",
    )
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, help_text="Type of SSO event"
    )
    payload_details = models.TextField(
        blank=True,
        help_text="SSO payload details (encoded or decoded) for debugging purposes",
    )
    signature = models.CharField(
        max_length=255, blank=True, help_text="The HMAC signature of the SSO payload"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the event was recorded"
    )

    def __str__(self):
        return f"SSO Event: {self.event_type} for {self.user} on {self.created_at:%Y-%m-%d %H:%M:%S}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SSO Event Log"
        verbose_name_plural = "SSO Event Logs"
