from django.apps import AppConfig


class CrudViewsPlainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_plain"

    def ready(self):
        pass
        # todo: run checks
        # import viewset.checks  # noqa
