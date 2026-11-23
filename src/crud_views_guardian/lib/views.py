from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import DEFAULT_DB_ALIAS, connections, router
from django.db.models import Count
from django.utils.translation import gettext as _

from crud_views.lib.ancestor_db import _check_nested_auth
from crud_views.lib.ancestors import _immediate_parent_access, _resolved_ancestor
from crud_views.lib.manage_report import SourceRecord, normalize_value
from crud_views.lib.settings import crud_views_settings
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
            protected=[obj for obj in related.protected if obj.pk in permitted(obj._meta.model, using=obj._state.db)],
        )


class _PermittedPks:
    """Request-local cache keyed by (model, candidate database).

    Use guardian's own content type and a bare codename; guardian derives the type from ``klass``. Models without
    a grantable view permission yield no pks for ordinary users (fail closed, D-07/D-08). Auto-created through
    tables are decided without touching ContentType: only authenticated active superusers see their rows, like
    the core view (D-05). That branch materializes the entire model's pk set once per projection, including
    unrelated through rows; it is not a bounded cascade-only query. Inactive actors get nothing.

    Supported projection requires co-located actor, auth joins, content types and configured Guardian grants.
    A route mismatch hides labels, including superuser/global/through fast paths; it never changes native blocking.
    This deliberately does not support central-auth grants for target rows on another database.
    """

    def __init__(self, user, accept_global: bool):
        self.user = user
        self.accept_global = accept_global
        self._cache: dict = {}

    @staticmethod
    def _routes_match(model, actor, using):
        """Validate the actual unbound managers/related paths used by installed Django and Guardian.

        Explicitly binding the candidate is insufficient: permission subqueries and SQL joins otherwise reuse
        colliding actor/content-type IDs. Check joins as tables, too, even though SQL executes on the outer DB.
        No query is evaluated here and through models never require a ContentType lookup.
        """
        from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
        from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

        user_model = get_user_model()
        models = {
            user_model,
            Group,
            Permission,
            ContentType,
            user_model._meta.get_field("groups").remote_field.through,
            user_model._meta.get_field("user_permissions").remote_field.through,
            Group._meta.get_field("permissions").remote_field.through,
            get_user_obj_perms_model(),
            get_group_obj_perms_model(),
        }
        # Guardian's per-target resolver may itself call the configured ContentType hook for direct grants.
        # Validate every enabled direct candidate from metadata first, so resolution cannot cross that boundary
        # before its auth/grant routes have been checked. The no-target resolvers above read configuration only.
        for field in model._meta.get_fields():
            if field.auto_created and (field.one_to_many or field.one_to_one):
                table = field.related_model
                if (
                    table is not None
                    and issubclass(table, (UserObjectPermissionBase, GroupObjectPermissionBase))
                    and getattr(table, "enabled", True)
                    and not table.objects.is_generic()
                ):
                    models.add(table)
        for table in models:
            # Guardian uses .objects, Django auth uses both default and related managers.
            for manager in (table.objects, table._default_manager, table._base_manager):
                if manager.all().db != using:
                    return False
            if router.db_for_read(table, instance=actor) != using:
                return False
        return all(
            qs.db == using
            for qs in (
                actor.groups.all(),
                actor.user_permissions.all(),
                Permission.objects.filter(group__in=actor.groups.all()),
                Group.permissions.through._default_manager.all(),
            )
        )

    def _projection_actor(self, model, *, using):
        """Resolve anonymous identity when configured; never substitute a colliding authenticated actor."""
        from guardian.conf import settings as guardian_settings
        from guardian.utils import get_anonymous_user

        actor = self.user
        if not getattr(actor, "is_authenticated", False):
            if not getattr(actor, "is_anonymous", False) or guardian_settings.ANONYMOUS_USER_NAME is None:
                return None
            # Validate the query route before Guardian's configured (possibly cached) resolver runs.
            if get_user_model().objects.all().db != using:
                return None
            try:
                actor = get_anonymous_user()
            except ObjectDoesNotExist:
                return None
        if (
            not isinstance(actor, get_user_model())
            or actor._state.adding
            or actor.pk is None
            or actor._state.db != using
            or not getattr(actor, "is_active", True)
        ):
            return None
        if not self._routes_match(model, actor, using):
            return None
        if len(connections.databases) > 1:
            # Unknown backend SQL paths cannot be certified by this finite topology predicate.
            if (
                using != DEFAULT_DB_ALIAS
                and self.accept_global
                and any(
                    backend
                    not in {
                        "django.contrib.auth.backends.ModelBackend",
                        "guardian.backends.ObjectPermissionBackend",
                    }
                    for backend in settings.AUTHENTICATION_BACKENDS
                )
            ):
                return None
            # Identity has already been verified. Reload only that same-alias identity to discard permission
            # and prefetch caches with unknown alias provenance; never replace request.user.
            try:
                actor = get_user_model()._default_manager.using(using).get(pk=actor.pk)
            except ObjectDoesNotExist:
                return None
            if not getattr(actor, "is_active", True) or not self._routes_match(model, actor, using):
                return None
        return actor

    def __call__(self, model, *, using) -> set:
        if _guardian_inactive_actor(self.user):
            return set()
        if not isinstance(using, str) or using not in connections:
            return set()
        key = (model, using)
        if key not in self._cache:
            candidates = model._default_manager.using(using).all()
            actor = self._projection_actor(model, using=using)
            if candidates.db != using or actor is None:
                self._cache[key] = set()
                return self._cache[key]
            opts = model._meta
            if opts.auto_created:
                self._cache[key] = set(candidates.values_list("pk", flat=True)) if actor.is_superuser else set()
                return self._cache[key]

            from guardian.ctypes import get_content_type
            from guardian.shortcuts import get_objects_for_user

            ct = get_content_type(model)
            if ct._state.db != using:
                self._cache[key] = set()
                return self._cache[key]
            codename = f"view_{ct.model}"
            qs = get_objects_for_user(actor, codename, klass=candidates, accept_global_perms=self.accept_global)
            self._cache[key] = set(qs.values_list("pk", flat=True)) if qs.db == using else set()
        return self._cache[key]


def _filter_tree(items: list, permitted: _PermittedPks) -> list:
    return [_filter_item(item, permitted) for item in items]


def _filter_item(item, permitted: _PermittedPks):
    """Keep permitted model objects, hide others as None, pass everything else through."""
    if isinstance(item, list):
        return _filter_tree(item, permitted)
    if item is not None and hasattr(item, "_meta"):
        return item if item.pk in permitted(item._meta.model, using=item._state.db) else None
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

    For child creates: the shared ancestor guard authorizes the ancestors (by default the immediate parent
    needs change; its own ViewSet provider decides how — object grants for a GuardianViewSet parent, model
    permissions for a core parent). No model-level add_<child> check is made. The parent is resolved and
    cv_action_enabled still runs with it, also when the parent is unprotected (provider "none").

    The permission helper for a nested create is cv_create_has_access. It uses the bounded immediate-parent
    rule (crud_views.lib.ancestors._immediate_parent_access): the immediate parent's provider with this
    create's nearest Write key, never a farther ancestor. It accepts the configured parent model instance,
    or an own-child instance of a single-FK nesting whose parent is resolved through ParentViewSet.attribute.
    Anything else denies. cv_has_access always returns False for a nested create: a create has no own object,
    and the parent rule does not belong in that hook's object argument.
    """

    @classmethod
    def _cv_page_link_ancestors(cls, rendering_view, page_obj):
        """Supply only the URL parent of an own child in a single-FK nesting, without a lookup."""
        parent = cls.cv_viewset.parent
        if parent is None:
            return super()._cv_page_link_ancestors(rendering_view, page_obj)
        # Keep denied: the child-list permission filter and M2M child page (D-27), the create page
        # itself and sibling button (D-33), and views without a resolved parent (D-16).
        # GuardianQuerysetMixin.cv_get_context supplies the child list page's URL parent itself.
        if not isinstance(page_obj, cls.cv_viewset.model) or parent.many_to_many_through_attribute:
            return ()
        resolved = _resolved_ancestor(rendering_view, parent.name)
        return (resolved,) if resolved is not None else ()

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
        Permission-only hook for links to this create, using its immediate parent's rule.

        This is the only own-permission step for every package control currently shown that links to a
        nested Guardian create. A sibling button to it and its create-page create control stay hidden
        without asking this hook. One existing list-page limit remains: when a nested Guardian list's own
        ViewSet registers a Guardian create under the same key, GuardianQuerysetMixin.cv_get_context gives
        a parent or sibling button to this create the page's own create result.

        The default applies the immediate parent's provider and fallback with this create's nearest Write
        key; provider "none" skips only that permission. An inactive signed-in actor is denied; an anonymous
        actor receives the parent provider's answer. The request-resolved parent identity is reused when
        available. Action state is evaluated separately. Override in subclasses for custom parent rules.

        Args:
            user: the requesting user
            rendering_view: the child list view for its create control, or the rendering view for a cancel
                target. It is None for child context buttons, card child actions, object navbar child items,
                parent buttons, create controls or create card actions on child object/card pages, and the
                cv_context_has_permission filter on a child object page. Overrides must not assume it is set.
            parent_obj: the resolved parent instance. An own child of a single-foreign-key nesting is also
                accepted and resolved to its parent; None, missing relations and every other input deny.
        """
        if cls.cv_viewset.parent is None:
            return cls.cv_has_access(user, None)
        if _guardian_inactive_actor(user):
            return False
        resolved = cls._cv_guardian_create_parent(parent_obj)
        return _immediate_parent_access(cls, user, resolved, rendering_view=rendering_view)

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Top-level create: check the model-level add permission through the base class.

        Nested create: return False for every argument. A create has no own object; use
        cv_create_has_access for its parent-based permission rule. Package links to a nested Guardian
        create do not call cv_has_access, so overriding it does not affect those links.
        """
        assert not isinstance(user, str)

        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        return False

    @classmethod
    def _cv_link_permission(cls, user, obj, parent_obj, *, rendering_view=None):
        """A nested create's permission is solely its documented parent-based hook.

        Keep that hook's actor rule, including anonymous backend grants under a model-provider parent
        (known limit L2, retained for stage 1).
        """
        if cls.cv_viewset.parent is None:
            return super()._cv_link_permission(user, obj, parent_obj, rendering_view=rendering_view)
        return cls.cv_create_has_access(user, rendering_view, parent_obj)


class GuardianManageView(ManageView):
    def _manage_class_source(self, viewset):
        if viewset.manage_view_class:
            return None
        if crud_views_settings.guardian_manage_view_class:
            return "CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS"
        return SourceRecord(code="default") if getattr(self, "_manage_export_enabled", False) else _("default")

    template_name = "crud_views/view_guardian_manage.html"

    def get_manage_checks(self, viewset, user):
        from crud_views_guardian.checks import collect_guardian_composition_checks

        data = super().get_manage_checks(viewset, user)
        messages = collect_guardian_composition_checks([viewset])
        helper = self._manage_check_messages
        data["messages"] += (
            self._manage_check_message_data(messages, export=True)
            if getattr(self, "_manage_export_enabled", False) and helper is ManageView._manage_check_messages
            else helper(messages)
        )
        return data

    def _guard_manage_auth(self, viewset, user):
        """Check the supplied model's configured grant routes before core diagnostics."""
        super()._guard_manage_auth(viewset, user)
        _check_nested_auth(viewset.get_view_class("manage"), actor=user, model=viewset.model, provider="guardian")

    def get_manage_actor_row(self, viewset, user):
        self._guard_manage_auth(viewset, user)
        row = super().get_manage_actor_row(viewset, user)
        for cell in row["cells"]:
            cell["object_count"] = viewset.get_objects_for_user(user, cell["key"]).count()
        return row

    def get_manage_permissions(self, viewset, user):
        from guardian.ctypes import get_content_type
        from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

        self._guard_manage_auth(viewset, user)
        data = super().get_manage_permissions(viewset, user)
        content_type = get_content_type(viewset.model)
        permissions = {
            f"{content_type.app_label}.{codename}": pk
            for pk, codename in Permission.objects.filter(content_type=content_type).values_list("pk", "codename")
        }
        permission_keys = {
            permissions[col["permission"]]: col["key"] for col in data["columns"] if col["permission"] in permissions
        }
        data["groups"] = self._manage_object_rows(
            data["columns"],
            data["groups"],
            get_group_obj_perms_model(viewset.model),
            "group",
            "name",
            content_type,
            permission_keys,
        )
        if data["show_users"]:
            users = self._manage_object_rows(
                data["columns"],
                data["users"] + data["users_overflow"],
                get_user_obj_perms_model(viewset.model),
                "user",
                get_user_model().USERNAME_FIELD,
                content_type,
                permission_keys,
            )
            data["users"], data["users_overflow"] = users[:20], users[20:]
        return data

    @staticmethod
    def _manage_object_rows(columns, model_rows, grant_model, holder, label_field, content_type, permission_keys):
        """Merge one aggregate per grant table into direct model holders, keyed by PK."""
        rows = {row["id"]: row for row in model_rows}
        grants = grant_model.objects.filter(permission_id__in=permission_keys)
        generic = grant_model.objects.is_generic()
        if generic:
            grants = grants.filter(content_type=content_type)
        counts = {"object_count": Count("object_pk" if generic else "content_object_id", distinct=True)}
        if holder == "group":
            counts["member_count"] = Count("group__user", distinct=True)
        for grant in grants.values(holder + "_id", holder + "__" + label_field, "permission_id").annotate(**counts):
            pk = grant[holder + "_id"]
            row = rows.setdefault(
                pk,
                {
                    "id": pk,
                    "label": grant[holder + "__" + label_field],
                    "member_count": grant.get("member_count"),
                    "cells": [{"key": col["key"], "model": False, "object_count": None} for col in columns],
                },
            )
            key = permission_keys[grant["permission_id"]]
            next(cell for cell in row["cells"] if cell["key"] == key)["object_count"] = grant["object_count"]
        return sorted(rows.values(), key=lambda row: (row["label"], row["id"]))

    def get_manage_guardian(self, viewset, user):
        """Fixed helper policy, independent of per-view and ancestor fallback."""
        from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY

        return {"get_objects_for_user": dict(STRICT_HELPER_POLICY)}

    def get_manage_views(self, viewset, user):
        self._guard_manage_auth(viewset, user)
        rows = super().get_manage_views(viewset, user)
        export = getattr(self, "_manage_export_enabled", False)
        for row in rows:
            view = viewset.get_view_class(row["key"])
            labels = [label for cls, label in GUARDIAN_MIXINS if issubclass(view, cls)]
            applicable = self._guardian_global_fallback_applicable(view)
            accept = bool(getattr(view, "cv_guardian_accept_global_perms", False)) if applicable else None
            policy_code = ("global_fallback" if accept else "strict") if applicable else "not_applicable"
            effective = (_("global fallback") if accept else _("strict")) if applicable else _("not applicable")
            row["parent_only_requirement"] = (
                viewset.parent is not None and issubclass(view, GuardianParentPermissionMixin) and not applicable
            )
            row["guardian_policy"] = {
                "applicable": applicable,
                "accept_global_perms": accept,
                "effective_policy": policy_code if export else effective,
                "tooltip": (
                    _("Visible rows are filtered by this permission; an empty list is allowed.")
                    if issubclass(view, GuardianQuerysetMixin)
                    else _("The object's permission is checked independently of ancestor policy.")
                    if applicable
                    else _("This view has no local Guardian object or queryset policy.")
                ),
            }
            if applicable:
                policy_help = (
                    _("Model permissions are accepted alongside object grants.")
                    if accept
                    else _("Global model permissions are not accepted.")
                )
                row["guardian_policy"]["tooltip"] = policy_help + " " + row["guardian_policy"]["tooltip"]
            section = next((s for s in row["sections"] if s["key"] == "guardian"), None)
            if section is None:
                section = {"key": "guardian", "label": _("Guardian"), "entries": [], "default_count": 0}
                row["sections"].insert(-1, section)
            section["entries"].insert(
                0,
                {
                    "key": "guardian_mixin",
                    "value": " + ".join(labels) if labels else "—",
                    "source": _("effective"),
                    "is_default": False,
                    "unknown": False,
                    **(
                        {
                            "_export": {
                                "value": normalize_value(
                                    [
                                        f"{cls.__module__}.{cls.__qualname__}"
                                        for cls, _label in GUARDIAN_MIXINS
                                        if issubclass(view, cls)
                                    ]
                                ),
                                "source": SourceRecord(code="effective"),
                            }
                        }
                        if export
                        else {}
                    ),
                },
            )
            section["entries"].append(
                {
                    "key": "effective_policy",
                    "value": effective,
                    "source": _("effective"),
                    "is_default": False,
                    "unknown": False,
                    **(
                        {
                            "_export": {
                                "value": normalize_value(policy_code),
                                "source": SourceRecord(code="effective"),
                            }
                        }
                        if export
                        else {}
                    ),
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        from crud_views.lib.ancestors import _effective_provider
        from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY

        context = super().get_context_data(**kwargs)
        context["manage_guardian"] = self.get_manage_guardian(self.cv_viewset, self.request.user)
        parent = self.cv_viewset.parent
        if parent is not None:
            parent_vs = parent.viewset
            fallback = " + model fallback" if parent_vs.ancestor_policy.accept_global_perms else ""
            parent_viewset_info = f"{parent_vs.name} (ancestor provider: {_effective_provider(parent_vs)}{fallback})"
        else:
            parent_viewset_info = None
        as_ancestor = context["ancestor_policy"]["as_ancestor"]
        context["guardian_config"] = {
            "parent_viewset": parent_viewset_info,
            # this ViewSet as an ancestor of nested requests: the effective values of the core "ancestor_policy"
            # entry (phase 06.18); local view options are reported per view in get_view_data()
            "ancestor_policy": {
                "provider": as_ancestor["effective_provider"],
                "accept_global_perms": as_ancestor["accept_global_perms"],
            },
            # the ViewSet helper's own fixed policy (D-05); global fallback is per view, see get_view_data()
            "get_objects_for_user": dict(STRICT_HELPER_POLICY),
        }
        return context

    def get_permission_holders(self):
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Count
        from guardian.models import GroupObjectPermission

        # nested: the grant tables (and Django's auth tables) must be on default before the first query (06.18)
        _check_nested_auth(self, actor=self.request.user, model=self.cv_viewset.model, provider="guardian")
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

        Only object and queryset views do (their local object gate / list filter). Parent-only views (nested
        create) no longer do: ancestors are gated by the shared ancestor policy, whose model fallback is the
        ancestor ViewSet's ``ancestor_policy.accept_global_perms``. Plain views, manage and top-level creates
        never do. The ViewSet is never consulted.
        """
        return issubclass(view_class, (GuardianObjectPermissionMixin, GuardianQuerysetMixin))
