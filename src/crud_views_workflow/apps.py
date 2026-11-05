from typing import ClassVar

from django.apps import AppConfig


class CrudViewsWorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_workflow"
    label = "cvw"

    crud_views_button_class_defaults: ClassVar[dict[str, str | None]] = {
        "workflow:badge-primary": "badge rounded-pill text-bg-primary",
        "workflow:badge-secondary": "badge rounded-pill text-bg-secondary",
        "workflow:badge-success": "badge rounded-pill text-bg-success",
        "workflow:badge-danger": "badge rounded-pill text-bg-danger",
        "workflow:badge-warning": "badge rounded-pill text-bg-warning",
        "workflow:badge-info": "badge rounded-pill text-bg-info",
        "workflow:badge-light": "badge rounded-pill text-bg-light",
        "workflow:badge-dark": "badge rounded-pill text-bg-dark",
        "workflow:history-wrapper": "table-responsive",
        "workflow:history-table": "table",
    }

    def ready(self):
        import crud_views_workflow.checks  # noqa
