from pydantic import model_validator
from typing_extensions import Self

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import ViewSet


class GuardianViewSet(ViewSet):
    """
    ViewSet subclass with per-object permission support via django-guardian.

    Attributes:
        cv_guardian_parent_permission: permission key checked on parent object
            for child list/detail/update/delete views. None = skip check.
        cv_guardian_parent_create_permission: permission key checked on parent
            object for child create views. None = falls back to
            cv_guardian_parent_permission.
    """

    cv_guardian_parent_permission: str | None = "view"
    cv_guardian_parent_create_permission: str | None = None
    cv_guardian_accept_global_perms: bool = False

    def get_manage_view_class(self):
        from django.utils.module_loading import import_string
        from crud_views_guardian.lib.views import GuardianManageView

        dotted = self.manage_view_class or crud_views_settings.guardian_manage_view_class
        if dotted:
            return import_string(dotted)
        return GuardianManageView

    @model_validator(mode="after")
    def register(self) -> Self:
        result = super().register()

        # Remove the base ManageView that super().register() just added so that the metaclass
        # can call register_view_class() without hitting the "already registered" guard.
        del self._views["manage"]

        base = self.get_manage_view_class()
        AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})

        return result

    def assign_perm(self, perm: str, user_or_group, obj) -> None:
        """Assign per-object permission using a short key ("view", "change", etc.)."""
        from guardian.shortcuts import assign_perm

        assign_perm(self.permissions[perm], user_or_group, obj)

    def remove_perm(self, perm: str, user_or_group, obj) -> None:
        """Remove per-object permission using a short key."""
        from guardian.shortcuts import remove_perm

        remove_perm(self.permissions[perm], user_or_group, obj)

    def get_objects_for_user(self, user, perm: str, qs=None):
        """Return queryset of objects for which user has the given per-object permission."""
        from guardian.shortcuts import get_objects_for_user

        return get_objects_for_user(
            user,
            self.permissions[perm],
            qs if qs is not None else self.model.objects.all(),
            accept_global_perms=False,
            use_groups=True,
        )
