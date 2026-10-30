from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Self

from pydantic import model_validator

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import ViewSet

# The fixed, non-configurable guardian arguments of GuardianViewSet.get_objects_for_user() (D-05). The manage page
# reports exactly these values, so its strict-helper entry cannot drift from the call.
STRICT_HELPER_POLICY = MappingProxyType({"policy": "strict", "accept_global_perms": False, "use_groups": True})

_REMOVED_GLOBAL_PERMS_KEY = "cv_guardian_accept_global_perms"
_REMOVED_GLOBAL_PERMS_MESSAGE = (
    "GuardianViewSet no longer accepts cv_guardian_accept_global_perms: it never affected access and was removed "
    "before 1.0. Set cv_guardian_accept_global_perms = True on each Guardian view class that should accept global "
    "model permissions. GuardianViewSet.get_objects_for_user() stays strict and has no global-permission option."
)


class GuardianViewSet(ViewSet):
    """
    ViewSet subclass with per-object permission support via django-guardian.

    Attributes:
        cv_guardian_parent_permission: permission key checked on parent object
            for child list/detail/update/delete views. None = skip check.
        cv_guardian_parent_create_permission: permission key checked on parent
            object for child create views. None = falls back to
            cv_guardian_parent_permission.

    Global model-permission fallback is configured per view class (``cv_guardian_accept_global_perms``), never on
    the ViewSet; passing the removed ViewSet key raises a validation error naming that replacement.
    """

    cv_guardian_parent_permission: str | None = "view"
    cv_guardian_parent_create_permission: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_removed_global_perms_flag(cls, data: Any) -> Any:
        """Reject the removed ViewSet flag before Pydantic would silently ignore it as an extra (D-04).

        Only mapping input is inspected; anything else (an existing instance, invalid input) passes through to
        Pydantic's established validation. Raising here precedes the after-validator, so nothing is registered.
        """
        if isinstance(data, Mapping) and _REMOVED_GLOBAL_PERMS_KEY in data:
            raise ValueError(_REMOVED_GLOBAL_PERMS_MESSAGE)
        return data

    def get_manage_view_class(self):
        from django.utils.module_loading import import_string

        from crud_views_guardian.lib.views import GuardianManageView

        dotted = self.manage_view_class or crud_views_settings.guardian_manage_view_class
        if dotted:
            return import_string(dotted)
        return GuardianManageView

    @model_validator(mode="after")
    def register(self) -> Self:
        if self.is_resource:
            raise ValueError(f"GuardianViewSet does not support Resource-based ViewSets (got {self.model!r})")

        result = super().register()

        # Remove the base ManageView that super().register() just added so that the metaclass
        # can call register_view_class() without hitting the "already registered" guard.
        del self._views["manage"]

        base = self.get_manage_view_class()
        _AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})

        return result

    def _resolve_permission_key(self, perm: str) -> str:
        """Resolve exact configured string keys before query access or permission changes."""
        permissions = self.permissions
        if not isinstance(perm, str) or perm not in permissions:
            alternatives = ", ".join(repr(key) for key in sorted(permissions))
            raise ValueError(f"Invalid permission key {perm!r}. Valid keys: {alternatives}.")
        return permissions[perm]

    def assign_perm(self, perm: str, user_or_group, obj) -> None:
        """Assign per-object permission using a short key ("view", "change", etc.)."""
        from guardian.shortcuts import assign_perm

        permission = self._resolve_permission_key(perm)
        assign_perm(permission, user_or_group, obj)

    def remove_perm(self, perm: str, user_or_group, obj) -> None:
        """Remove per-object permission using a short key."""
        from guardian.shortcuts import remove_perm

        permission = self._resolve_permission_key(perm)
        remove_perm(permission, user_or_group, obj)

    def get_objects_for_user(self, user, perm: str, qs=None):
        """Return queryset of objects for which user has the given per-object permission.

        Strict: global model permissions are not accepted. Object and group grants count, an active superuser
        gets every object, and an inactive (authenticated) user gets none.
        """
        from guardian.shortcuts import get_objects_for_user

        from crud_views_guardian.lib.mixins import _guardian_inactive_actor

        permission = self._resolve_permission_key(perm)
        qs = qs if qs is not None else self.model.objects.all()
        if _guardian_inactive_actor(user):
            return qs.none()
        return get_objects_for_user(
            user,
            permission,
            qs,
            accept_global_perms=STRICT_HELPER_POLICY["accept_global_perms"],
            use_groups=STRICT_HELPER_POLICY["use_groups"],
        )
