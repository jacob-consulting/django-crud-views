from django.core.checks import Error, register

from crud_views.lib import viewset as registry
from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin


@register("crud_views", "crud_views_guardian")
def check_guardian_composition(app_configs=None, **kwargs):
    """Parent authorization cannot replace the child object's or queryset's gate."""
    with registry._REGISTRY_LOCK:
        viewsets = list(registry._REGISTRY.values())

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
