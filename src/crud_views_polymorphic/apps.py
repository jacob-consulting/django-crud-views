from django.apps import AppConfig


class CrudViewsPolymorphicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_polymorphic"
    label = "cvp"

    def ready(self):
        # nothing to wire up at startup; kept as the extension point for app initialisation
        pass
