import logging

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from crud_views.lib.ancestor_db import _check_nested_auth
from crud_views.lib.ancestors import _immediate_parent_access, _resolved_parent
from crud_views.lib.view import CrudView

logger = logging.getLogger(__name__)


def _guardian_inactive_actor(user) -> bool:
    """True for an authenticated user whose account is inactive (D-11).

    Guardian's ``get_objects_for_user`` ignores ``is_active`` (an inactive superuser gets every row), so each
    Guardian request gate and callable query/access helper denies such actors explicitly. Anonymous users are
    not "inactive actors" here; their configured anonymous behavior applies unchanged.
    """
    return bool(getattr(user, "is_authenticated", False)) and not getattr(user, "is_active", True)


def _guardian_actor_response(view):
    """Guardian's explicit actor rules, with or without protected ancestry: an anonymous actor gets the view's
    configured ``cv_guardian_anonymous_behavior`` (login redirect, or raise 403/404), an authenticated inactive
    actor 403. None for an active authenticated actor. Loads nothing."""
    user = view.request.user
    if not user.is_authenticated:
        behavior = getattr(view, "cv_guardian_anonymous_behavior", "redirect")
        if behavior == "404":
            raise Http404
        if behavior == "403":
            raise PermissionDenied
        return view.handle_no_permission()  # redirect to login
    if _guardian_inactive_actor(user):
        raise PermissionDenied
    return None


def _local_permission_name(view) -> str:
    """The full permission name for a Guardian view instance's own ``cv_permission`` key (request gates only).

    Raises ImproperlyConfigured when the key has no entry in the ViewSet's permission map — typically a model
    whose migration has not run — so no Guardian checker or shortcut ever receives ``None`` (G-06.18-2).
    """
    viewset = view.cv_viewset
    key = view.cv_permission
    permission = viewset.permissions.get(key)
    if not permission:
        raise ImproperlyConfigured(
            f"ViewSet {viewset.name!r} view {view.cv_key!r}: permission key {key!r} is not in the ViewSet's "
            f"permission map — if the model is new, run `manage.py migrate`; "
            f"a server started before the migration may need a restart"
        )
    return permission


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

    A cv_permission key missing from the ViewSet's permission map (e.g. an unapplied migration) makes
    get_object() raise ImproperlyConfigured and cv_has_access() return False for every actor.
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    @classmethod
    def _cv_cancel_target_available(cls, user, obj, rendering_view):
        if not user.is_authenticated or _guardian_inactive_actor(user):
            return False
        return super()._cv_cancel_target_available(user, obj, rendering_view)

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

    def _cv_ancestor_actor_response(self, *, protected: bool):
        # nested requests: Guardian's explicit actor rules in both ancestry modes (phase 06.18)
        return _guardian_actor_response(self)

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

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # nested: the gate's auth records must be on default, before the vocabulary and any shortcut (06.18)
        _check_nested_auth(self, actor=self.request.user, model=type(obj), obj=obj, provider="guardian")
        perm = _local_permission_name(self)
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
        _check_nested_auth(cls, actor=user, model=cls.cv_viewset.model, obj=obj, provider="guardian")
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        if not perm:
            return False
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

    Overrides cv_has_access() to return True for every active actor without a
    model permission — the list page is always accessible; queryset filtering is
    the sole gate. This ensures "list" and "parent" context action buttons are
    visible regardless of whether an object is provided.

    A cv_permission key missing from the ViewSet's permission map (e.g. an unapplied migration) makes
    get_queryset() raise ImproperlyConfigured instead of returning any rows, and cv_has_access() return False
    for every actor.
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    @classmethod
    def _cv_cancel_target_available(cls, user, obj, rendering_view):
        if not user.is_authenticated or _guardian_inactive_actor(user):
            return False
        # Entry is allowed even with zero visible rows; never test queryset truthiness.
        return super()._cv_cancel_target_available(user, obj, rendering_view)

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

    def _cv_ancestor_actor_response(self, *, protected: bool):
        # nested requests: Guardian's explicit actor rules in both ancestry modes (phase 06.18)
        return _guardian_actor_response(self)

    @classmethod
    def cv_has_access(cls, user, obj=None):
        if _guardian_inactive_actor(user):
            return False
        # nested: the vocabulary read must be on default, as the core and object helpers require (06.18)
        _check_nested_auth(cls, actor=user, model=cls.cv_viewset.model)
        # a missing key hides the link, as the core helper does; the request itself raises in get_queryset()
        return bool(cls.cv_viewset.permissions.get(cls.cv_permission))

    @classmethod
    def _cv_child_link_has_access(cls, user, parent_obj):
        if not cls.cv_viewset.has_parent:
            return super()._cv_child_link_has_access(user, parent_obj)
        if not user.is_authenticated or _guardian_inactive_actor(user):
            return False
        access = super()._cv_child_link_has_access(user, parent_obj)
        if not access:
            return access
        # Standalone queryset compositions never checked the parent for their links (bounded migration).
        if not issubclass(cls, GuardianParentPermissionMixin):
            return access
        return _immediate_parent_access(cls, user, parent_obj)

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
        # nested: the filter's auth records must be on default, before the vocabulary and any shortcut (06.18)
        _check_nested_auth(self, actor=self.request.user, model=qs.model, provider="guardian")
        perm = _local_permission_name(self)
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

    In dispatch(), before any other processing: incomplete compositions raise ImproperlyConfigured, anonymous
    actors get the configured ``cv_guardian_anonymous_behavior`` response and inactive actors 403. A nested
    request then runs the shared ancestor guard (``crud_views.lib.ancestors``): each selected ancestor is gated
    by its own ViewSet's provider and ``ancestor_policy`` (a ``GuardianViewSet`` ancestor: strict object
    permissions, model fallback only with its own ``accept_global_perms``; a core ancestor: model permissions).
    No-op for top-level views.

    When a parent viewset is present, overrides has_permission() to return True so that Django's model-level
    PermissionRequiredMixin is bypassed (nested Guardian create has no child-add requirement). Object child views
    must also include GuardianObjectPermissionMixin; list child views must include GuardianQuerysetMixin.
    Incomplete compositions are reported by system check E001.

    The endpoint view's ``cv_guardian_accept_global_perms`` keeps only its local meaning (object gate, list
    filter); it never relaxes an ancestor. No-object child views (create, list) still run their independent
    cv_action_enabled state gate with the resolved immediate parent, also when that parent is unprotected.
    """

    # Policy names read via getattr() below. Annotation-only on purpose: a value here
    # would shadow an object/queryset mixin composed after this one (MRO order), while
    # the annotation still makes the names known to the W280 unknown-attribute check.
    cv_guardian_accept_global_perms: bool
    cv_guardian_anonymous_behavior: str

    @classmethod
    def _cv_cancel_target_available(cls, user, obj, rendering_view):
        error = cls._guardian_child_composition_error()
        if error:
            raise ImproperlyConfigured(error)
        if not user.is_authenticated or _guardian_inactive_actor(user):
            return False
        if cls.cv_viewset.parent is None:
            return super()._cv_cancel_target_available(user, obj, rendering_view)

        parent_obj = rendering_view._cv_cancel_parent_object()
        if not _immediate_parent_access(cls, user, parent_obj, rendering_view=rendering_view):
            return False
        if cls.cv_object:
            if not cls.cv_has_access(user, obj):
                return False
            action_obj = obj
        else:
            if not cls._cv_cancel_parent_target_access(user, rendering_view, parent_obj):
                return False
            # Parent-only views bypass child/model permission exactly as dispatch does.
            action_obj = parent_obj
        return cls._cv_action_enabled_for_rendering(user, action_obj, rendering_view)

    @classmethod
    def _cv_cancel_parent_target_access(cls, user, rendering_view, parent_obj):
        if issubclass(cls, GuardianQuerysetMixin):
            return cls.cv_has_access(user, None)
        if hasattr(cls, "cv_create_has_access"):
            return cls.cv_create_has_access(user, rendering_view, parent_obj)
        return True

    @classmethod
    def _guardian_child_composition_error(cls):
        """Name a missing child gate without loading objects or evaluating permission policy."""
        if cls.cv_viewset.parent is None:
            return None
        mro = cls.__mro__
        if cls.cv_object:
            if not issubclass(cls, GuardianObjectPermissionMixin):
                return "Object child views using GuardianParentPermissionMixin require GuardianObjectPermissionMixin."
            # SingleObjectMixin.get_object() does not call super(): a later Guardian gate is unreachable.
            if SingleObjectMixin in mro and mro.index(GuardianObjectPermissionMixin) > mro.index(SingleObjectMixin):
                return "Place GuardianObjectPermissionMixin before the core object view class."
        if issubclass(cls, MultipleObjectMixin):
            if not issubclass(cls, GuardianQuerysetMixin):
                return "List child views using GuardianParentPermissionMixin require GuardianQuerysetMixin."
            # Both implementations terminate queryset loading; filtering must wrap them, not follow them.
            if any(
                terminal in mro and mro.index(GuardianQuerysetMixin) > mro.index(terminal)
                for terminal in (CrudView, MultipleObjectMixin)
            ):
                return "Place GuardianQuerysetMixin before the core list view class."
        return None

    def _guardian_validate_child_composition(self):
        error = self._guardian_child_composition_error()
        if error:
            raise ImproperlyConfigured(error)

    def has_permission(self):
        self._guardian_validate_child_composition()
        if self.cv_viewset.parent is not None:
            return True
        return super().has_permission()

    def dispatch(self, request, *args, **kwargs):
        self._guardian_validate_child_composition()
        if self.cv_viewset.parent is not None:
            # the shared ancestor guard (crud_views.lib.ancestors) is the only ancestor traversal: static validation
            # first, then Guardian's actor rules (anonymous/inactive, via _cv_ancestor_actor_response), then the
            # ancestors — all before any object/queryset/state work; CrudView.dispatch() reuses its result
            response = self._cv_ancestor_guard()
            if response is not None:
                return response
            # Secondary state gate — only for no-object child views (e.g. create), whose action object IS the
            # immediate parent the guard just resolved (read directly, not through the overridable
            # cv_get_parent_object() hook, as the pre-06.18 dispatch did with its own lookup). Object child views
            # (detail/update/delete) carry a row and are gated in get_object() with that row, so they must NOT also
            # be gated here with the parent (that would invoke cv_action_enabled with the wrong object type).
            if not self.cv_object and not self.cv_action_enabled(request.user, _resolved_parent(self)):
                raise PermissionDenied
            return super().dispatch(request, *args, **kwargs)
        # top-level: the guard does nothing, so Guardian's actor rules apply here
        if not request.user.is_authenticated:
            return self._guardian_deny_anonymous()
        if _guardian_inactive_actor(request.user):
            raise PermissionDenied  # before any None-policy, method or fragment handling (D-11)
        return super().dispatch(request, *args, **kwargs)

    def _cv_ancestor_actor_response(self, *, protected: bool):
        # nested requests: the guard calls this after static validation (D-32), in both ancestry modes
        return _guardian_actor_response(self)

    def _guardian_deny_anonymous(self):
        return _guardian_actor_response(self)
