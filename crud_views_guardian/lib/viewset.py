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
