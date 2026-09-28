from django.apps import AppConfig


class CrudViewsGuardianConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_guardian"
    label = "cvg"

    def ready(self):
        # nothing to wire up at startup; kept as the extension point for app initialisation
        pass
