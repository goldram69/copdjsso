# apps/discourse/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.discourse.api import sync_user_with_discourse
from .models import DiscourseProfile

User = get_user_model()


@receiver(post_save, sender=User)
def sync_user_on_create_or_update(sender, instance, created, **kwargs):
    """Automatically sync new or updated users with Discourse."""
    sync_user_with_discourse(instance)  # Sync after creation/update
