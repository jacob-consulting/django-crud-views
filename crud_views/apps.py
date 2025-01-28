from django.apps import AppConfig


class CrudViewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crud_views'

    def ready(self):
        import crud_views.checks  # noqa
