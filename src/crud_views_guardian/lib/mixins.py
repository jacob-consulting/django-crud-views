import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


def _guardian_inactive_actor(user) -> bool:
    """True for an authenticated user whose account is inactive (D-11).

    Guardian's ``get_objects_for_user`` ignores ``is_active`` (an inactive superuser gets every row), so each
    Guardian request gate and callable query/access helper denies such actors explicitly. Anonymous users are
    not "inactive actors" here; their configured anonymous behavior applies unchanged.
    """
    return bool(getattr(user, "is_authenticated", False)) and not getattr(user, "is_active", True)


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
        if _guardian_inactive_actor(self.request.user):
            raise PermissionDenied
        return True

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if _guardian_inactive_actor(user):
            return False
        # Check model-level perm first (without obj — ModelBackend returns empty
        # set when obj is passed, so we must call has_perm without obj here).
        if self.cv_guardian_accept_global_perms and user.has_perm(perm):
            return True
        from guardian.core import ObjectPermissionChecker

        checker = ObjectPermissionChecker(user)
        return checker.has_perm(perm.split(".")[1], obj)

    def get_object(self):
        obj = super().get_object()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        if not self._check_object_perm(self.request.user, perm, obj):
            raise PermissionDenied
        # Secondary state gate — deny a disabled action even with object perm.
        if not self.cv_action_enabled(self.request.user, obj):
            raise PermissionDenied
        return obj

    @classmethod
    def cv_has_access(cls, user, obj=None):
        if _guardian_inactive_actor(user):
            return False
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        if obj is not None:
            # Model-level perm must be checked without obj (ModelBackend ignores
            # obj and returns empty set when obj is passed).
            if cls.cv_guardian_accept_global_perms and user.has_perm(perm):
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
        if _guardian_inactive_actor(self.request.user):
            raise PermissionDenied
        return True

    @classmethod
    def cv_has_access(cls, user, obj=None):
        return not _guardian_inactive_actor(user)

    def cv_get_context(self, key=None, obj=None, user=None, request=None, *, location=None):
        """
        Override to fix create button visibility for child viewsets under guardian.

        cv_has_access() is a classmethod with no access to the request or URL
        kwargs. When a create context action is rendered from a list page, obj=None
        and the parent object cannot be determined inside cv_has_access() alone.

        This override detects that situation (obj=None, target is a child create
        view, viewset has a parent), resolves the parent object from self.kwargs
        using the existing cv_get_parent_object() helper, and delegates to
        target_cls.cv_create_has_access() with the resolved parent. The result
        replaces cv_access in the already-built context dict. cv_action_enabled is
        re-derived separately from the same parent through the target's state
        adapter; when the parent cannot be resolved both fields are False and no
        custom state hook is called with None. No other context fields are affected.
        """
        assert not isinstance(user, str)

        ctx = super().cv_get_context(key=key, obj=obj, user=user, request=request, location=location)

        if obj is None and key is not None and self.cv_viewset.has_parent:
            # A custom ContextButton may target the create view via key_target while
            # using a different key (e.g. a second, differently-styled create button).
            # Resolve key_target so the create-access re-derivation finds the view.
            context_button = self.cv_get_context_button(key)
            target_key = context_button.key_target if context_button and context_button.key_target else key
            if self.cv_viewset.is_view_registered(target_key):
                target_cls = self.cv_viewset.get_view_class(target_key)
            else:
                target_cls = None
            if (
                target_cls
                and getattr(target_cls, "cv_permission", None) == "add"
                and hasattr(target_cls, "cv_create_has_access")
            ):
                try:
                    parent_obj = self.cv_get_parent_object()
                except (Http404, KeyError):
                    logger.warning(
                        "could not resolve parent object for create button visibility at %s",
                        self,
                        exc_info=True,
                    )
                    parent_obj = None
                ctx["cv_access"] = target_cls.cv_create_has_access(user, self, parent_obj)
                # state is independent of permission; an unresolved parent never reaches a custom state hook
                ctx["cv_action_enabled"] = parent_obj is not None and target_cls._cv_action_enabled_for_context(
                    user, parent_obj
                )

        return ctx

    def get_queryset(self):
        from guardian.shortcuts import get_objects_for_user

        qs = super().get_queryset()
        if _guardian_inactive_actor(self.request.user):
            return qs.none()
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
    from the combined view class: when set, a model-level permission on the
    parent model is accepted as a fallback for the per-object one.

    When a parent viewset is present, overrides has_permission() to return True
    so that Django's model-level PermissionRequiredMixin is bypassed; the parent
    object-level check in dispatch() is the sole gatekeeper.

    A parent permission key of None disables only the parent *permission* check:
    the URL parent is still resolved (a missing parent is a 404) and no-object
    child views (create) still run their independent cv_action_enabled state gate
    with that parent. No child-add permission is required instead.
    """

    # Policy names read via getattr() below. Annotation-only on purpose: a value here
    # would shadow an object/queryset mixin composed after this one (MRO order), while
    # the annotation still makes the names known to the W280 unknown-attribute check.
    cv_guardian_accept_global_perms: bool
    cv_guardian_anonymous_behavior: str

    def has_permission(self):
        if self.cv_viewset.parent is not None:
            return True
        return super().has_permission()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self._guardian_deny_anonymous()
        if _guardian_inactive_actor(request.user):
            raise PermissionDenied  # before any parent, None-policy, method or fragment handling (D-11)
        parent_vs = self.cv_viewset.parent
        if parent_vs is not None:
            self._guardian_check_parent(request.user, parent_vs, kwargs)
        return super().dispatch(request, *args, **kwargs)

    def _guardian_deny_anonymous(self):
        behavior = getattr(self, "cv_guardian_anonymous_behavior", "redirect")
        if behavior == "404":
            raise Http404
        if behavior == "403":
            raise PermissionDenied
        return self.handle_no_permission()  # redirect to login

    @classmethod
    def _guardian_resolve_parent_perm_key(cls) -> str | None:
        """The parent permission key for this view class: create views use
        cv_guardian_parent_create_permission, falling back (when None) to
        cv_guardian_parent_permission. None means: no parent permission check."""
        perm_key = None
        if getattr(cls, "cv_permission", None) == "add":
            perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
        if perm_key is None:
            perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
        return perm_key

    def _guardian_parent_perm_key(self) -> str | None:
        return self._guardian_resolve_parent_perm_key()

    @classmethod
    def _guardian_user_has_parent_perm(cls, user, parent_obj) -> bool:
        """Whether ``user`` holds this view's parent permission on the resolved ``parent_obj``.

        Shared by dispatch and the create access helpers. A None permission key skips only this
        permission evaluation (True); parent resolution and action state are the callers' concern.
        Inactive actors are always denied.
        """
        if _guardian_inactive_actor(user):
            return False
        perm_key = cls._guardian_resolve_parent_perm_key()
        if perm_key is None:
            return True
        parent_perm = cls.cv_viewset.parent.viewset.permissions.get(perm_key)
        # accept_global: the model-level permission is a fallback. Note that
        # user.has_perm(perm, obj) would NOT do this — Django's ModelBackend returns
        # nothing once an object is passed, and guardian checks object perms only.
        if getattr(cls, "cv_guardian_accept_global_perms", False) and user.has_perm(parent_perm):
            return True
        from guardian.core import ObjectPermissionChecker

        return ObjectPermissionChecker(user).has_perm(parent_perm.split(".")[1], parent_obj)

    def _guardian_check_parent(self, user, parent_vs, kwargs):
        """Resolve the URL parent (404 when missing) and raise PermissionDenied unless ``user`` may act on it."""
        parent_obj = get_object_or_404(parent_vs.viewset.model, pk=kwargs.get(parent_vs.get_pk_name()))
        if not self._guardian_user_has_parent_perm(user, parent_obj):
            raise PermissionDenied
        # Secondary state gate — only for no-object child views (e.g. create),
        # whose action object IS the parent. It runs even when the parent
        # permission key is None (D-10). Object child-views (detail/update/
        # delete) carry a row and are gated in get_object() with that row, so we
        # must NOT also gate them here with the parent (that would invoke
        # cv_action_enabled with the wrong object type).
        if not self.cv_object and not self.cv_action_enabled(user, parent_obj):
            raise PermissionDenied
