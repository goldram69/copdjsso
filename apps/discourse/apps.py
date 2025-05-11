from django.apps import AppConfig


class DiscourseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.discourse'

    def ready(self):
        # Import signals so that the receivers are registered.
        import apps.discourse.signals
