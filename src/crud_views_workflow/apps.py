from django.apps import AppConfig


class CrudViewsWorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_workflow"
    label = "cvw"

    def ready(self):
        # import crud_views.checks  # noqa
        pass
