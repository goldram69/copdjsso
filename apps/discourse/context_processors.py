# apps/discourse/context_processors.py
from django.conf import settings


def discourse_forum_url(request):
    """
    Adds the forum's base URL to every template context.
    """
    return {
        "forum_url": settings.DISCOURSE_INSTANCE_URL,
    }
