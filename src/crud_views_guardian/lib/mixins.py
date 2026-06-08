from django.core.exceptions import PermissionDenied
from django.http import Http404
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

    Overrides has_permission() to always return True — model-level permission is
    not required; all access control is delegated to get_object().
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    def has_permission(self):
        if not self.request.user.is_authenticated:
            if self.cv_guardian_anonymous_behavior == "404":
                raise Http404
            if self.cv_guardian_anonymous_behavior == "403":
                raise PermissionDenied
            return False  # triggers Django's handle_no_permission() → redirect to login
        return True

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if self.cv_guardian_accept_global_perms:
            # Check model-level perm first (without obj — ModelBackend returns empty
            # set when obj is passed, so we must call has_perm without obj here).
            if user.has_perm(perm):
                return True
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
                # Model-level perm must be checked without obj (ModelBackend ignores
                # obj and returns empty set when obj is passed).
                if user.has_perm(perm):
                    return True
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

    Overrides has_permission() to always return True — queryset filtering is
    the sole access control mechanism for list views.

    Overrides cv_has_access() to always return True — the list page is always
    accessible; queryset filtering is the sole gate. This ensures "list" and
    "parent" context action buttons are always visible regardless of whether
    an object is provided.
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    def has_permission(self):
        if not self.request.user.is_authenticated:
            if self.cv_guardian_anonymous_behavior == "404":
                raise Http404
            if self.cv_guardian_anonymous_behavior == "403":
                raise PermissionDenied
            return False  # triggers Django's handle_no_permission() → redirect to login
        return True

    @classmethod
    def cv_has_access(cls, user, obj=None):
        return True

    def cv_get_context(self, key=None, obj=None, user=None, request=None):
        """
        Override to fix create button visibility for child viewsets under guardian.

        cv_has_access() is a classmethod with no access to the request or URL
        kwargs. When a create context action is rendered from a list page, obj=None
        and the parent object cannot be determined inside cv_has_access() alone.

        This override detects that situation (obj=None, target is a child create
        view, viewset has a parent), resolves the parent object from self.kwargs
        using the existing cv_get_parent_object() helper, and delegates to
        target_cls.cv_create_has_access() with the resolved parent. The result
        replaces cv_access in the already-built context dict — no other context
        fields are affected.
        """
        assert not isinstance(user, str)

        ctx = super().cv_get_context(key=key, obj=obj, user=user, request=request)

        if obj is None and key is not None and self.cv_viewset.has_parent:
            if self.cv_viewset.is_view_registered(key):
                target_cls = self.cv_viewset.get_view_class(key)
            else:
                target_cls = None
            if target_cls and getattr(target_cls, "cv_permission", None) == "add":
                if hasattr(target_cls, "cv_create_has_access"):
                    try:
                        parent_obj = self.cv_get_parent_object()
                    except Exception:
                        parent_obj = None
                    ctx["cv_access"] = target_cls.cv_create_has_access(user, self, parent_obj)

        return ctx

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

    When a parent viewset is present, overrides has_permission() to return True
    so that Django's model-level PermissionRequiredMixin is bypassed; the parent
    object-level check in dispatch() is the sole gatekeeper.
    """

    def has_permission(self):
        if self.cv_viewset.parent is not None:
            return True
        return super().has_permission()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            behavior = getattr(self, "cv_guardian_anonymous_behavior", "redirect")
            if behavior == "404":
                raise Http404
            if behavior == "403":
                raise PermissionDenied
            return self.handle_no_permission()  # redirect to login
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
