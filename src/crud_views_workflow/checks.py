import importlib.util

from django.apps import apps
from django.core.checks import Error, register

TAG = "crud_views_workflow"


def _importable(name: str) -> bool:
    """True if the named top-level module can be imported."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


@register(TAG)
def check_workflow_dependencies(app_configs=None, **kwargs):
    """Error when crud_views_workflow is installed but its runtime deps are missing."""
    errors = []
    if not apps.is_installed("crud_views_workflow"):
        return errors
    if not _importable("django_fsm"):
        errors.append(
            Error(
                "django-fsm-2 is required by crud_views_workflow but is not installed.",
                hint="Install the optional extra: pip install django-crud-views[workflow]",
                id="crud_views_workflow.E001",
            )
        )
    if not _importable("fsm_admin"):
        errors.append(
            Error(
                "django-fsm-2-admin is required by crud_views_workflow but is not installed.",
                hint="Install the optional extra: pip install django-crud-views[workflow]",
                id="crud_views_workflow.E002",
            )
        )
    return errors
