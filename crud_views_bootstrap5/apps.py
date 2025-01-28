from django.apps import AppConfig


class CrudViewsBootstrap5Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crud_views_bootstrap5'

    def ready(self):
        pass
        # todo: run checks
        # import viewset.checks  # noqa
