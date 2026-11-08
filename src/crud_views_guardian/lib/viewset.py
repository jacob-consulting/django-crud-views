from collections import OrderedDict
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, ClassVar, Literal, Self

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

_REMOVED_PARENT_FIELDS = ("cv_guardian_parent_permission", "cv_guardian_parent_create_permission")
_REMOVED_PARENT_MESSAGE = (
    "GuardianViewSet no longer accepts {name}{where}: parent permissions are checked by ancestor authorization. "
    "Remove it and declare the requirement on the nested ViewSet with ancestor_policy=AncestorPolicy(read=..., "
    "write=..., actions={{...}}) using AncestorPermissions(nearest=..., higher=...); for a parent without a "
    'permission check set ancestor_policy=AncestorPolicy(provider="none") on the parent ViewSet. See '
    "docs/migrating-1.0.md."
)


def _declares(cls: type, name: str) -> bool:
    """Whether a (user) subclass declares ``name``: a Pydantic field, a class variable or a plain class attribute,
    also inherited. The framework classes no longer define either removed name."""
    return name in cls.model_fields or name in cls.__class_vars__ or hasattr(cls, name)


class GuardianViewSet(ViewSet):
    """
    ViewSet subclass with per-object permission support via django-guardian.

    As an ancestor of a nested ViewSet it requires the selected permission on the resolved object by default
    (provider ``"guardian"``); ``ancestor_policy`` chooses another provider or accepts model permissions too. The
    removed parent fields ``cv_guardian_parent_permission`` / ``cv_guardian_parent_create_permission`` are rejected.

    Global model-permission fallback of a view's own local gate is configured per view class
    (``cv_guardian_accept_global_perms``), never on the ViewSet; passing the removed ViewSet key raises a validation
    error naming that replacement.
    """

    _ANCESTOR_PROVIDERS: ClassVar[tuple[str, ...]] = ("model", "guardian", "none")

    @model_validator(mode="before")
    @classmethod
    def reject_removed_declarations(cls, data: Any) -> Any:
        """Reject removed declarations before Pydantic would silently ignore them (D-04).

        Constructor input: the removed ViewSet flag and both removed parent fields. A subclass declaring a removed
        parent field (field, class variable or attribute, inherited too) is rejected on construction. Anything else
        passes through to Pydantic's established validation. Raising here precedes the after-validator, so nothing
        is registered.
        """
        if isinstance(data, Mapping) and _REMOVED_GLOBAL_PERMS_KEY in data:
            raise ValueError(_REMOVED_GLOBAL_PERMS_MESSAGE)
        for name in _REMOVED_PARENT_FIELDS:
            if isinstance(data, Mapping) and name in data:
                raise ValueError(_REMOVED_PARENT_MESSAGE.format(name=name, where=""))
            if _declares(cls, name):
                raise ValueError(_REMOVED_PARENT_MESSAGE.format(name=name, where=f" (declared on {cls.__name__})"))
        return data

    def _ancestor_provider(self) -> Literal["model", "guardian", "none"]:
        """As an ancestor, a GuardianViewSet defaults to strict object permissions."""
        return self.ancestor_policy.provider or "guardian"

    def _ancestor_has_permission(self, user, obj, permission: str) -> bool:
        """The ``"guardian"`` provider: the object permission on ``obj`` (direct or group grant, Guardian's
        content-type semantics); ``ancestor_policy.accept_global_perms`` also accepts the model permission, checked
        separately without ``obj`` (Django's model backend grants nothing once an object is passed). Inactive actors
        are denied; an active superuser follows the backends. The checker lives for this call only. An explicit
        ``"model"`` provider uses the core model check."""
        if self._ancestor_provider() != "guardian":
            return super()._ancestor_has_permission(user, obj, permission)
        from guardian.core import ObjectPermissionChecker

        from crud_views_guardian.lib.mixins import _guardian_inactive_actor

        if _guardian_inactive_actor(user):
            return False
        if self.ancestor_policy.accept_global_perms and user.has_perm(permission):
            return True
        # the full "app_label.codename": Guardian drops the label itself and resolves the content type of ``obj``
        # through its configured resolver
        return ObjectPermissionChecker(user).has_perm(permission, obj)

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

    @property
    def default_permissions(self) -> OrderedDict[str, str]:
        """Discover permissions in Guardian's configured content-type namespace.

        Like the core ViewSet, retain nonempty results for the process lifetime and retry empty discovery.
        Resolver or permission changes after discovery require a fresh ViewSet or process restart.
        """
        from django.contrib.auth.models import Permission
        from guardian.ctypes import get_content_type

        if self._default_permissions is not None:
            return self._default_permissions
        content_type = get_content_type(self.model)
        permissions = OrderedDict()
        for permission in Permission.objects.filter(content_type=content_type):
            action = permission.codename.removesuffix(f"_{content_type.model}")
            permissions[action] = f"{content_type.app_label}.{permission.codename}"
        if permissions:
            self._default_permissions = permissions
        return permissions

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
