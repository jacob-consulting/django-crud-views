from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


class GuardianObjectPermissionMixin:
    """
    For single-object views (Detail, Update, Delete, Action).

    Hooks into get_object(): after the object is loaded, checks per-object
    permission. Raises 403 on denial.

    cv_guardian_accept_global_perms = False (default): uses ObjectPermissionChecker
    which checks only guardian's object-level tables — no model-level fallback.
    Set to True to use user.has_perm(perm, obj) which includes model-level fallback.

    Also overrides cv_has_access() so per-row action buttons in list views
    reflect per-object access correctly.
    """

    cv_guardian_accept_global_perms: bool = False

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if self.cv_guardian_accept_global_perms:
            return user.has_perm(perm, obj)
        from guardian.core import ObjectPermissionChecker

        checker = ObjectPermissionChecker(user)
        return checker.has_perm(perm.split(".")[1], obj)

    def get_object(self):
        obj = super().get_object()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        if not self._check_object_perm(self.request.user, perm, obj):
            raise PermissionDenied
        return obj

    @classmethod
    def cv_has_access(cls, user, obj=None):
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        if obj is not None:
            if cls.cv_guardian_accept_global_perms:
                return user.has_perm(perm, obj)
            from guardian.core import ObjectPermissionChecker

            checker = ObjectPermissionChecker(user)
            return checker.has_perm(perm.split(".")[1], obj)
        return False


class GuardianQuerysetMixin:
    """
    For list views.

    Filters get_queryset() to only objects the user has per-object permission on,
    via guardian's get_objects_for_user().

    cv_guardian_accept_global_perms = False (default): strict — only objects
    with an explicit per-object grant are returned.
    Set to True to also include objects accessible via model-level permission.
    """

    cv_guardian_accept_global_perms: bool = False

    def get_queryset(self):
        from guardian.shortcuts import get_objects_for_user

        qs = super().get_queryset()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        return get_objects_for_user(
            self.request.user,
            perm,
            qs,
            accept_global_perms=self.cv_guardian_accept_global_perms,
            use_groups=True,
        )


class GuardianParentPermissionMixin:
    """
    For child viewset views (any view type where cv_viewset.parent is set).

    In dispatch(), before any other processing, checks per-object permission
    on the parent instance. Raises 403 if denied. No-op when cv_viewset.parent
    is None.

    Reads cv_guardian_parent_permission / cv_guardian_parent_create_permission
    from the child GuardianViewSet. Respects cv_guardian_accept_global_perms
    from the combined view class.
    """

    def dispatch(self, request, *args, **kwargs):
        parent_vs = self.cv_viewset.parent
        if parent_vs is not None:
            is_create = getattr(self, "cv_permission", None) == "add"
            perm_key = None
            if is_create:
                perm_key = getattr(self.cv_viewset, "cv_guardian_parent_create_permission", None)
            if perm_key is None:
                perm_key = getattr(self.cv_viewset, "cv_guardian_parent_permission", "view")

            if perm_key is not None:
                parent_pk = kwargs.get(parent_vs.get_pk_name())
                parent_obj = get_object_or_404(parent_vs.viewset.model, pk=parent_pk)
                parent_perm = parent_vs.viewset.permissions.get(perm_key)
                accept_global = getattr(self, "cv_guardian_accept_global_perms", False)
                if accept_global:
                    has_perm = request.user.has_perm(parent_perm, parent_obj)
                else:
                    from guardian.core import ObjectPermissionChecker

                    checker = ObjectPermissionChecker(request.user)
                    has_perm = checker.has_perm(parent_perm.split(".")[1], parent_obj)
                if not has_perm:
                    raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
