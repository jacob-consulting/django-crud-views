from django.core.checks import Error, register
from django.core.checks import Warning as DjangoWarning
from django.utils.translation import gettext

from crud_views.lib import viewset as registry
from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin


@register("crud_views", "crud_views_guardian")
def check_guardian_composition(app_configs=None, **kwargs):
    """Parent authorization cannot replace the child object's or queryset's gate."""
    with registry._REGISTRY_LOCK:
        viewsets = list(registry._REGISTRY.values())
    return collect_guardian_composition_checks(viewsets)


def collect_guardian_composition_checks(viewsets) -> list:
    """Collect child-gate composition errors only for the supplied ViewSets."""
    messages = []
    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            if not issubclass(view, GuardianParentPermissionMixin):
                continue
            error = view._guardian_child_composition_error()
            if error:
                messages.append(
                    Error(
                        error,
                        hint="Use the corresponding shipped Guardian view, or add the required "
                        "GuardianObjectPermissionMixin / GuardianQuerysetMixin before the core view class.",
                        obj=view,
                        id="crud_views_guardian.E001",
                    )
                )
    return messages


@register("crud_views", "crud_views_guardian")
def check_guardian_bulk(app_configs=None, **kwargs):
    """Load URL-registered actions before collecting the startup-only bulk warning."""
    from crud_views.checks import _url_configuration_loaded

    _url_configuration_loaded()
    with registry._REGISTRY_LOCK:
        viewsets = list(registry._REGISTRY.values())
    return collect_guardian_bulk_checks(viewsets)


def collect_guardian_bulk_checks(viewsets) -> list:
    """Warn when bulk actions rely on queryset scoping instead of an item permission hook."""
    from crud_views.lib.bulk import BulkFormViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet

    messages = []
    for viewset in viewsets:
        if not isinstance(viewset, GuardianViewSet):
            continue
        for view in viewset.get_all_views().values():
            if (
                issubclass(view, BulkFormViewPermissionRequired)
                and view.cv_bulk_has_permission is BulkFormViewPermissionRequired.cv_bulk_has_permission
            ):
                messages.append(
                    DjangoWarning(
                        gettext(
                            "Bulk action in a GuardianViewSet does not override cv_bulk_has_permission: "
                            "every record its queryset shows is treated as permitted."
                        ),
                        hint=gettext(
                            "Implement cv_bulk_has_permission with the object permission check, "
                            "or narrow get_queryset() and silence crud_views_guardian.W002."
                        ),
                        obj=view,
                        id="crud_views_guardian.W002",
                    )
                )
    return messages
