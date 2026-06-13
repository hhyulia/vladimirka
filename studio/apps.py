from django.apps import AppConfig


class StudioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'studio'
    verbose_name = 'Танцевальная студия'

    def ready(self):
        import studio.signals  # noqa: F401
