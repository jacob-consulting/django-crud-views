from django.core.exceptions import ObjectDoesNotExist

from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CardListViewPermissionRequired,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.manage import ManageView
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianParentPermissionMixin,
    GuardianQuerysetMixin,
    _guardian_inactive_actor,
)

GUARDIAN_MIXINS = [
    (GuardianObjectPermissionMixin, "ObjectPermissionMixin"),
    (GuardianQuerysetMixin, "QuerysetMixin"),
    (GuardianParentPermissionMixin, "ParentMixin"),
]


class GuardianDetailViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailViewPermissionRequired
):
    pass


class GuardianUpdateViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired
):
    pass


class GuardianDeleteRelatedObjectsMixin:
    """Filter cascade-delete related objects and protected-object labels by per-object view permissions via
    django-guardian (with the view's ``cv_guardian_accept_global_perms`` fallback).

    Replaces the core model-level filter rather than chaining to it, so an object grant keeps its label without a
    global view permission. Protected objects are filtered even when the cascade tree is empty; the blocked state
    itself is captured by ``DeleteView.get_context_data`` before this hook runs, and summaries stay unchanged.
    """

    def cv_filter_related_objects(self, user, related):
        from crud_views.lib.views.delete import RelatedObjects

        permitted = _PermittedPks(user, getattr(self, "cv_guardian_accept_global_perms", False))
        return RelatedObjects(
            tree=_filter_tree(related.tree, permitted),
            summary=related.summary,
            protected=[obj for obj in related.protected if obj.pk in permitted(obj._meta.model)],
        )


class _PermittedPks:
    """Request-local, per-model cache of viewable pks (one instance per projection).

    Use guardian's own content type and a bare codename; guardian derives the type from ``klass``. Models without
    a grantable view permission yield no pks for ordinary users (fail closed, D-07/D-08). Auto-created through
    tables are decided without touching ContentType: only authenticated active superusers see their rows, like
    the core view (D-05). That branch materializes the entire model's pk set once per projection, including
    unrelated through rows; it is not a bounded cascade-only query. Inactive actors get nothing.
    """

    def __init__(self, user, accept_global: bool):
        self.user = user
        self.accept_global = accept_global
        self._cache: dict = {}

    def __call__(self, model) -> set:
        if _guardian_inactive_actor(self.user):
            return set()
        if model not in self._cache:
            opts = model._meta
            if opts.auto_created:
                self._cache[model] = (
                    set(model._default_manager.values_list("pk", flat=True))
                    if getattr(self.user, "is_authenticated", False) and getattr(self.user, "is_superuser", False)
                    else set()
                )
                return self._cache[model]

            from guardian.ctypes import get_content_type
            from guardian.shortcuts import get_objects_for_user

            ct = get_content_type(model)
            codename = f"view_{ct.model}"
            qs = get_objects_for_user(self.user, codename, klass=model, accept_global_perms=self.accept_global)
            self._cache[model] = set(qs.values_list("pk", flat=True))
        return self._cache[model]


def _filter_tree(items: list, permitted: _PermittedPks) -> list:
    return [_filter_item(item, permitted) for item in items]


def _filter_item(item, permitted: _PermittedPks):
    """Keep permitted model objects, hide others as None, pass everything else through."""
    if isinstance(item, list):
        return _filter_tree(item, permitted)
    if item is not None and hasattr(item, "_meta"):
        return item if item.pk in permitted(item._meta.model) else None
    return item


class GuardianDeleteViewPermissionRequired(
    GuardianDeleteRelatedObjectsMixin,
    GuardianParentPermissionMixin,
    GuardianObjectPermissionMixin,
    DeleteViewPermissionRequired,
):
    pass


class GuardianActionViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, ActionViewPermissionRequired
):
    pass


class GuardianListViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianQuerysetMixin, ListViewPermissionRequired
):
    pass


class GuardianCardListViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianQuerysetMixin, CardListViewPermissionRequired
):
    pass


class GuardianCreateViewPermissionRequired(GuardianParentPermissionMixin, CreateViewPermissionRequired):
    """
    For top-level creates: GuardianParentPermissionMixin is a no-op (no parent).
    Django's PermissionRequiredMixin checks model-level add_<model> permission.

    For child creates: GuardianParentPermissionMixin checks per-object permission
    on the parent instance using cv_guardian_parent_create_permission (falls back
    to cv_guardian_parent_permission). No model-level add_<child> check is made.
    When the resolved key is None only that permission check is skipped; the
    parent is still resolved and cv_action_enabled still runs with it.

    The access helpers (cv_has_access, cv_create_has_access) are permission-only
    and share the dispatch permission rule. They accept the configured parent
    model instance, or an own-child instance of a single-FK nesting whose parent
    is resolved through ParentViewSet.attribute. Anything else denies.
    """

    @classmethod
    def _cv_guardian_create_parent(cls, obj):
        """The configured parent instance an access/state input stands for, or None.

        - an instance of the parent model is the parent itself (also for M2M nesting, when supplied explicitly);
        - an instance of this view's own model resolves its FK parent via ``ParentViewSet.get_attribute()``,
          only for single-FK nesting: an M2M child may belong to several parents and names none of them;
        - a missing/None relation (Django ``ObjectDoesNotExist``), a non-parent result and every other
          input yield None. No attribute name or related manager is guessed.
        """
        if obj is None:
            return None
        parent = cls.cv_viewset.parent
        parent_model = parent.viewset.model
        if isinstance(obj, parent_model):
            return obj
        if not isinstance(obj, cls.cv_viewset.model) or parent.many_to_many_through_attribute:
            return None
        try:
            candidate = getattr(obj, parent.get_attribute())
        except ObjectDoesNotExist:
            return None
        return candidate if isinstance(candidate, parent_model) else None

    @classmethod
    def _cv_action_enabled_for_context(cls, user, obj=None) -> bool:
        """Nested create: the action object is the parent. Resolve it from ``obj`` (parent or FK own child);
        unresolved → False without calling a custom cv_action_enabled hook. Top-level: unchanged."""
        if cls.cv_viewset.parent is None:
            return super()._cv_action_enabled_for_context(user, obj)
        parent_obj = cls._cv_guardian_create_parent(obj)
        if parent_obj is None:
            return False
        return cls.cv_action_enabled(user, parent_obj)

    @classmethod
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        """
        Determine whether the create button should be visible for this child viewset.

        Called by GuardianQuerysetMixin.cv_get_context() when rendering the create
        context action from a list view where obj=None. The list view resolves the
        parent object from its URL kwargs and passes it here.

        Default implementation checks cv_guardian_parent_create_permission (falling
        back to cv_guardian_parent_permission) on the parent object — the same rule
        dispatch applies, including the accept-global fallback and a None key
        (no permission check). Permission only: the action state is resolved
        separately. Override in subclasses for custom logic.

        Args:
            user: the requesting user
            rendering_view: the view instance that is rendering the button
                (e.g. NetzwerkMemberListView) — provides access to
                rendering_view.request, rendering_view.kwargs, etc.
                Not used by the default implementation; available for subclass overrides.
            parent_obj: the resolved parent model instance (an own-child instance of a
                single-FK nesting is resolved to its parent), or None if resolution
                failed (returns False in that case, as does any other object)
        """
        if cls.cv_viewset.parent is None:
            return cls.cv_has_access(user, None)
        if _guardian_inactive_actor(user):
            return False
        resolved = cls._cv_guardian_create_parent(parent_obj)
        if resolved is None:
            return False
        return cls._guardian_user_has_parent_perm(user, resolved)

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Permission check for create button visibility.

        Case 1 — Top-level create (cv_viewset.parent is None):
            Falls through to the base class, which checks the model-level
            add_<model> permission. Top-level creates intentionally require a
            model-level grant; there is no parent object to check against.

        Case 2 — Child create, no object (obj=None, e.g. book list page):
            Returns False. GuardianQuerysetMixin.cv_get_context() handles the
            real check by resolving the parent from URL kwargs and calling
            cv_create_has_access(). This is a safe fallback for any call path
            that bypasses the list view override.

        Case 3 — Child create, parent object available (e.g. publisher detail page):
            When obj is an instance of the parent model, checks
            cv_guardian_parent_create_permission (falling back to
            cv_guardian_parent_permission) on that specific parent object, with the
            same rule as dispatch (accept-global fallback; a None key skips the
            permission check). "add book" only appears for parent objects the user
            is actually allowed to create children under.

        Case 4 — Child create, own-child object (e.g. a book detail page):
            For single-FK nesting the book's configured parent attribute is
            resolved and Case 3 applies to that parent. M2M nesting cannot name a
            single parent from a child and denies.

        Any other object (an unrelated model, a child without its parent
        relation) denies — it cannot establish which parent the create would
        bind to. This supersedes the former permissive fallback to True.
        """
        assert not isinstance(user, str)

        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None or _guardian_inactive_actor(user):
            return False  # safe fallback — GuardianQuerysetMixin.cv_get_context handles the real check

        parent_obj = cls._cv_guardian_create_parent(obj)
        if parent_obj is None:
            return False
        return cls._guardian_user_has_parent_perm(user, parent_obj)


class GuardianManageView(ManageView):
    template_name = "crud_views/view_guardian_manage.html"

    def get_context_data(self, **kwargs):
        from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY

        context = super().get_context_data(**kwargs)
        parent = self.cv_viewset.parent
        if parent is not None:
            parent_vs = parent.viewset
            perm_key = self.cv_viewset.cv_guardian_parent_permission
            perm_codename = (
                parent_vs.permissions.get(perm_key, perm_key).split(".")[-1] if perm_key is not None else None
            )
            parent_viewset_info = (
                f"{parent_vs.name} ({perm_codename} → guardian)"
                if perm_codename is not None
                else f"{parent_vs.name} (no permission)"
            )
        else:
            parent_viewset_info = None
        context["guardian_config"] = {
            "cv_guardian_parent_permission": self.cv_viewset.cv_guardian_parent_permission,
            "cv_guardian_parent_create_permission": self.cv_viewset.cv_guardian_parent_create_permission,
            "parent_viewset": parent_viewset_info,
            # the ViewSet helper's own fixed policy (D-05); global fallback is per view, see get_view_data()
            "get_objects_for_user": dict(STRICT_HELPER_POLICY),
        }
        return context

    def get_permission_holders(self):
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Count
        from guardian.models import GroupObjectPermission

        holders = {(r["group"], r["permission"]): r for r in super().get_permission_holders()}

        ct = ContentType.objects.get_for_model(self.cv_viewset.model)
        codename_to_key = {perm.split(".")[1]: key for key, perm in self.cv_viewset.permissions.items()}

        qs = (
            GroupObjectPermission.objects.filter(permission__content_type=ct)
            .values("group__name", "permission__codename")
            .annotate(object_count=Count("object_pk", distinct=True))
        )
        for row in qs:
            group_name = row["group__name"]
            perm_key = codename_to_key.get(row["permission__codename"])
            if perm_key is None:
                continue
            k = (group_name, perm_key)
            if k in holders:
                holders[k]["object_count"] = row["object_count"]
            else:
                holders[k] = {
                    "group": group_name,
                    "permission": perm_key,
                    "has_model_perm": False,
                    "object_count": row["object_count"],
                    "users": [],
                }

        return sorted(holders.values(), key=lambda r: (r["group"], r["permission"]))

    def get_view_data(self):
        from collections import OrderedDict

        data = super().get_view_data()
        for key, view_data in data.items():
            view_class = self.cv_viewset.get_all_views()[key]
            labels = [label for cls, label in GUARDIAN_MIXINS if issubclass(view_class, cls)]
            view_data["base"]["guardian_mixin"] = " + ".join(labels) if labels else "—"
            applicable = self._guardian_global_fallback_applicable(view_class)
            accept = bool(getattr(view_class, "cv_guardian_accept_global_perms", False)) if applicable else None
            effective = ("global fallback" if accept else "strict") if applicable else "not applicable"
            view_data["guardian_policy"] = OrderedDict(
                {
                    "global_fallback_applicable": applicable,
                    "cv_guardian_accept_global_perms": accept,
                    "effective_policy": effective,
                }
            )
        return data

    def _guardian_global_fallback_applicable(self, view_class) -> bool:
        """Whether ``view_class`` ever consults its own ``cv_guardian_accept_global_perms`` (D-06).

        Object and queryset views always do. A parent-only view does so only in its parent check, i.e. with an
        actual parent and a non-None effective parent permission (the shared resolver used by dispatch and the
        create helpers). Plain views, manage and top-level creates never do. The ViewSet is never consulted.
        """
        if issubclass(view_class, (GuardianObjectPermissionMixin, GuardianQuerysetMixin)):
            return True
        if issubclass(view_class, GuardianParentPermissionMixin) and self.cv_viewset.parent is not None:
            return view_class._guardian_resolve_parent_perm_key() is not None
        return False
