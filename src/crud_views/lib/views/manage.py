import inspect
from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count, Q
from django.urls import NoReverseMatch, reverse
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.ancestor_db import _check_nested_auth
from crud_views.lib.check import (
    CheckUnknownAttributes,
    _collect_cv_names,
    _is_config_value,
    _project_cv_declarations,
    _registry_vocabulary,
)
from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView


class ManageView(PermissionRequiredMixin, CrudView, generic.TemplateView):
    template_name = "crud_views/view_manage.html"
    manage_docs_base_url = "https://django-crud-views.readthedocs.io/en/stable/reference/manage/"

    cv_pk: bool = False  # does not need primary key
    cv_key = "manage"
    cv_path = "manage"
    cv_object = False

    cv_context_actions = crud_views_settings.manage_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/manage.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/manage.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/manage.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/manage.html"

    # icons
    cv_icon_action = "manage"
    cv_icon_header = "manage"

    def dispatch(self, request, *args, **kwargs):
        # Nested manage: ancestry first (phase 06.18), then the local settings/group gate that
        # PermissionRequiredMixin.dispatch runs through has_permission().
        response = self._cv_ancestor_guard()
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def _cv_manage_allowed(cls, user) -> bool:
        """Diagnostics require an active developer in every enabled mode."""
        from django.conf import settings as django_settings

        if not user.is_authenticated or not user.is_active:
            return False
        mode = crud_views_settings.manage_views_enabled
        if mode == "no" or (mode == "debug_only" and not django_settings.DEBUG):
            return False
        # Validate reached nested auth reads before the membership query, including action projection.
        _check_nested_auth(cls, actor=user, model=cls.cv_viewset.model)
        return user.groups.filter(name=crud_views_settings.manage_group).exists()

    def _cv_ancestor_actor_response(self, *, protected: bool):
        """Reject anonymous/inactive actors before lookup, including all-none ancestry."""
        from crud_views.lib.ancestors import _protected_actor_response

        return _protected_actor_response(self)

    def has_permission(self):
        return self._cv_manage_allowed(self.request.user)

    @classmethod
    def cv_get_requirement(cls) -> dict:
        custom = cls._cv_requirement_is_custom()
        return {
            "kind": "custom" if custom else "group",
            "value": None if custom else crud_views_settings.manage_group,
            "ancestor_applies": True,
        }

    @classmethod
    def cv_has_access(cls, user, obj=None) -> bool:
        return cls._cv_manage_allowed(user)

    @classmethod
    def cv_get_inaccessible_actions(cls) -> str:
        return "hide"

    def get_permission_holders(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        _check_nested_auth(self, actor=self.request.user, model=self.cv_viewset.model)
        user_model = get_user_model()
        rows = []
        for key, perm in self.cv_viewset.permissions.items():
            app_label, codename = perm.split(".")
            users = []
            if crud_views_settings.manage_show_users:
                users = list(
                    user_model.objects.filter(
                        user_permissions__codename=codename,
                        user_permissions__content_type__app_label=app_label,
                    )
                    .values_list("username", flat=True)
                    .order_by("username")
                )
            for group in Group.objects.filter(
                permissions__codename=codename,
                permissions__content_type__app_label=app_label,
            ).order_by("name"):
                rows.append(
                    {
                        "group": group.name,
                        "permission": key,
                        "has_model_perm": True,
                        "object_count": None,
                        "users": users,
                    }
                )
        return rows

    def _guard_manage_auth(self, viewset, user):
        """Use the supplied ViewSet's routing contract before reading diagnostic auth data."""
        manage_class = viewset.get_all_views().get("manage")
        if manage_class is None:
            raise ImproperlyConfigured("Manage diagnostics require a registered manage view")
        _check_nested_auth(manage_class, actor=user, model=viewset.model)

    def get_manage_actor_row(self, viewset, user):
        """The supplied actor's effective grants; this does not authorize a request."""
        self._guard_manage_auth(viewset, user)
        return {
            "id": user.pk,
            "label": user.get_username(),
            "member_count": None,
            "cells": [
                {"key": key, "model": user.has_perm(permission), "object_count": None}
                for key, permission in viewset.permissions.items()
            ],
        }

    def get_manage_permissions(self, viewset, user):
        """Prepare ordered matrix data without depending on a request instance."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        self._guard_manage_auth(viewset, user)
        columns = [
            {"key": key, "permission": permission, "codename": permission.split(".", 1)[1]}
            for key, permission in viewset.permissions.items()
        ]
        groups = self._manage_direct_rows(columns, Group.objects.all(), "permissions", "name")
        member_counts = dict(
            Group.objects.filter(pk__in=[row["id"] for row in groups])
            .annotate(member_count=Count("user"))
            .values_list("pk", "member_count")
        )
        for row in groups:
            row["member_count"] = member_counts[row["id"]]
        user_model = get_user_model()
        show_users = crud_views_settings.manage_show_users
        users = (
            self._manage_direct_rows(columns, user_model.objects.all(), "user_permissions", user_model.USERNAME_FIELD)
            if show_users
            else []
        )
        superusers = user_model.objects.filter(is_active=True, is_superuser=True)
        return {
            "columns": columns,
            "actor": self.get_manage_actor_row(viewset, user),
            "groups": groups,
            "users": users[:20],
            "show_users": show_users,
            "superusers": {
                "count": superusers.count(),
                "names": list(
                    superusers.order_by(user_model.USERNAME_FIELD, "pk").values_list(
                        user_model.USERNAME_FIELD, flat=True
                    )
                )
                if show_users
                else [],
            },
            "users_overflow": users[20:],
        }

    @staticmethod
    def _manage_direct_rows(columns, queryset, relation, label_field):
        """One query per holder kind; labels sort rows, primary keys identify them."""
        if not columns:
            return []
        matching = Q()
        for column in columns:
            app, codename = column["permission"].split(".", 1)
            matching |= Q(**{f"{relation}__content_type__app_label": app, f"{relation}__codename": codename})
        holders = {}
        for pk, label, app, codename in (
            queryset.filter(matching)
            .order_by(label_field, "pk")
            .values_list("pk", label_field, f"{relation}__content_type__app_label", f"{relation}__codename")
        ):
            holder = holders.setdefault(pk, {"id": pk, "label": label, "grants": set()})
            holder["grants"].add(f"{app}.{codename}")
        return [
            {
                "id": holder["id"],
                "label": holder["label"],
                "member_count": None,
                "cells": [
                    {"key": col["key"], "model": col["permission"] in holder["grants"], "object_count": None}
                    for col in columns
                ],
            }
            for holder in holders.values()
        ]

    def get_manage_routes(self, viewset, user):
        """One display projection of generated routes; never reverse example object URLs."""
        from django.contrib.admindocs.views import simplify_regex

        views = viewset.get_all_views()
        if not views:
            return []
        try:
            patterns = {pattern.name: str(pattern.pattern) for pattern in viewset.urlpatterns}
        except (ImproperlyConfigured, ViewSetError):
            patterns = {}
        rows = []
        for key in views:
            name = viewset.get_router_name(key)
            pattern = patterns.get(name)
            rows.append(
                {
                    "key": key,
                    "name": name,
                    "route": simplify_regex(pattern) if pattern is not None else None,
                    "route_error": None if pattern is not None else _("Route unavailable; review system checks"),
                }
            )
        return rows

    @staticmethod
    def _manage_display(value):
        if isinstance(value, type):
            return f"{value.__module__}.{value.__qualname__}"
        display = repr(value)
        return display[:200] + "…" if len(display) > 200 else display

    def _manage_field(self, viewset, key, value, source=None):
        is_default = key not in viewset._manage_constructor_fields
        return {
            "key": key,
            "value": self._manage_display(value),
            "source": source or (_("default") if is_default else _("set")),
            "is_default": is_default,
        }

    def get_manage_facts(self, viewset, user):
        """Effective identity with constructor provenance independent of value source."""
        rows = []
        for key in (
            "name",
            "prefix",
            "pk",
            "pk_name",
            "app",
            "model",
            "parent",
            "verbose_name",
            "verbose_name_plural",
            "ordering",
            "icon_header",
        ):
            value = getattr(viewset, key)
            source = None
            if key in {"verbose_name", "verbose_name_plural", "ordering"} and value is None:
                value = getattr(viewset.model._meta, key, None)
                source = _("model Meta")
            elif key == "pk" and key not in viewset._manage_constructor_fields:
                source = _("model Meta")
            row = self._manage_field(viewset, key, value, source)
            if key in {"verbose_name", "verbose_name_plural"}:
                row["value"] = str(value)
            if key == "icon_header":
                row["icon"] = value
            rows.append(row)
        return rows

    def _manage_hierarchy_item(self, viewset, user):
        route = next((row for row in self.get_manage_routes(viewset, user) if row["key"] == "manage"), None)
        return {
            "name": viewset.name,
            "model": self._manage_display(viewset.model),
            "resource": viewset.is_resource,
            "route_name": route["name"] if route else None,
            "route": route["route"] if route else None,
            "route_error": route["route_error"] if route else None,
            "url": None,
        }

    def get_manage_hierarchy(self, viewset, user, *, route_kwargs=None):
        """Only upward links, using supplied URL coordinates and no object reads."""
        from crud_views.lib.ancestors import _walk_ancestors
        from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

        data = {"parents": [], "children": [], "route_error": None}
        try:
            chain = _walk_ancestors(viewset)
        except (ImproperlyConfigured, ViewSetError):
            chain = []
            data["route_error"] = _("Route unavailable; review system checks")
        for _edge, parent in chain:
            item = self._manage_hierarchy_item(parent, user)
            if item["route_name"] and not item["route_error"]:
                try:
                    required = parent.get_parent_url_args()
                    if all(key in (route_kwargs or {}) for key in required):
                        item["url"] = reverse(item["route_name"], kwargs={key: route_kwargs[key] for key in required})
                except (NoReverseMatch, ImproperlyConfigured, ViewSetError):
                    item["route_error"] = _("Route unavailable; review system checks")
            data["parents"].append(item)
        with _REGISTRY_LOCK:
            children = [child for child in _REGISTRY.values() if child.parent and child.parent.name == viewset.name]
        data["children"] = [self._manage_hierarchy_item(child, user) for child in children]
        return data

    def _manage_requirement(self, viewset, user, view):
        """Resolve presentation metadata narrowly; auth/database failures remain visible."""
        from crud_views.lib.ancestors import _operation_requirements, _selected_gates, _validate_ancestor_structure

        errors = []
        parent = None
        requirement = {"kind": "custom", "value": None, "ancestor_applies": True}
        try:
            requirement = view.cv_get_requirement()
            if requirement["ancestor_applies"] and viewset.parent is not None:
                chain = _validate_ancestor_structure(viewset)
                pair = _operation_requirements(view)
                selected = _selected_gates(viewset, chain)
                if selected:
                    index = next(iter(selected))
                    key = getattr(pair, selected[index])
                    if key is not None:
                        parent = {"key": key, "ancestor": chain[index][1]}
        except ImproperlyConfigured:
            errors.append(_("Requirement unavailable; review system checks"))

        # Keep routing guards and permission map access outside the presentation-only catch.
        permission = None
        if requirement["kind"] == "permission":
            self._guard_manage_auth(viewset, user)
            permission = viewset.permissions.get(requirement["value"])
            if permission is None:
                errors.append(_("Undeclared permission key: %(key)s") % {"key": requirement["value"]})
        if parent is not None:
            self._guard_manage_auth(viewset, user)
            ancestor = parent.pop("ancestor")
            _check_nested_auth(view, actor=user, model=ancestor.model)
            parent["permission"] = ancestor.permissions.get(parent["key"])
            if parent["permission"] is None:
                errors.append(_("Undeclared ancestor permission key: %(key)s") % {"key": parent["key"]})
        return {
            "requirement": requirement,
            "permission": permission,
            "parent_requirement": parent,
            "requirement_metadata_error": "; ".join(errors) or None,
        }

    def get_manage_views(self, viewset, user):
        """Project registered class facts directly; legacy overrides remain independent."""
        routes = {row["key"]: row for row in self.get_manage_routes(viewset, user)}
        return [
            {
                "key": key,
                "route_name": routes[key]["name"],
                "route": routes[key]["route"],
                "route_error": routes[key]["route_error"],
                **self._manage_requirement(viewset, user, view),
                "guardian_policy": None,
                "class_path": f"{view.__module__}.{view.__qualname__}",
                "sections": self._manage_view_sections(view),
            }
            for key, view in viewset.get_all_views().items()
        ]

    def _manage_view_sections(self, view):
        all_names, data_names = set(), set()
        for klass in view.__mro__:
            _collect_cv_names(klass, all_names, data_names, include_classes=True)
        # An overriding descriptor/method must not expose a base's data or be invoked.
        missing = object()
        values = {name: inspect.getattr_static(view, name, missing) for name in data_names - {"cv_viewset"}}
        values = {name: value for name, value in values.items() if _is_config_value(value) or isinstance(value, type)}
        declarations = _project_cv_declarations(view, include_classes=True, exclude_generated=True)
        checker = CheckUnknownAttributes(context=view)
        registry_names = _registry_vocabulary()[0]
        context_names = checker._context_names()[0]
        unknown = checker._suspects() - registry_names - context_names - checker._allowlist()
        navigation = [
            "cv_context_actions",
            "cv_list_actions",
            "cv_home_key",
            "cv_success_key",
            "cv_success_keys",
            "cv_cancel_key",
            "cv_cancel_keys",
            "cv_list_action_method",
            "cv_backend_only",
        ]
        groups = [
            ("navigation", _("Navigation"), navigation),
            ("templates", _("Templates"), sorted(name for name in values if "_template" in name)),
            ("icons", _("Icons"), ["cv_icon_action", "cv_icon_header"]),
        ]
        guardian = sorted(name for name in values if name.startswith("cv_guardian_"))
        if guardian:
            groups.append(("guardian", _("Guardian"), guardian))
        curated = {name for _, _, names in groups for name in names}
        groups.append(("other", _("Other"), sorted(values.keys() - curated)))
        sections = []
        for key, label, names in groups:
            entries = [
                self._manage_view_entry(view, name, values[name], declarations, unknown, missing)
                for name in names
                if name in values
            ]
            sections.append(
                {
                    "key": key,
                    "label": label,
                    "entries": entries,
                    "default_count": sum(entry["is_default"] for entry in entries),
                }
            )
        return sections

    @staticmethod
    def _manage_view_entry(view, name, value, declarations, unknown, missing):
        owner = declarations.get(name)
        source = _("default") if owner is None else (_("set") if owner is view else _("inherited"))
        # Only known, request-independent fallback paths. Empty/False are values, not missing data.
        field = name.removeprefix("cv_")
        layered = {
            "list_actions_inline",
            "context_actions_inline",
            "card_actions_inline",
            "list_actions_label_mode",
            "context_actions_label_mode",
            "form_actions_label_mode",
            "inaccessible_actions",
        }
        if value is None and field in layered:
            viewset_value = getattr(view.cv_viewset, field)
            value = CrudView.cv_first_inline_keys.__func__(view, value, field)
            source = _("from ViewSet") if viewset_value is not None else _("global setting")
        elif value is None and field in {"icon_header", "context_buttons", "extends_template"}:
            viewset_field = "extends" if field == "extends_template" else field
            value = getattr(view.cv_viewset, viewset_field)
            source = _("from ViewSet")
            if field == "extends_template" and value is None:
                value = crud_views_settings.extends
                source = _("global setting")
        if value is missing:
            display = _("not declared")
            source = _("not declared")
        elif isinstance(value, type):
            display = f"{value.__module__}.{value.__qualname__}"
        else:
            display = repr(value)
            if len(display) > 200:
                display = display[:200] + "…"
        return {
            "key": field,
            "value": display,
            "source": source,
            "is_default": owner is None,
            "unknown": name in unknown,
        }

    def _get_permission_data(self):
        _check_nested_auth(self, actor=self.request.user, model=self.cv_viewset.model)
        return [
            {"viewset": key, "django": permission, "has_permission": self.request.user.has_perm(permission)}
            for key, permission in self.cv_viewset.permissions.items()
        ]

    @staticmethod
    def _manage_check_messages(messages):
        """Prepare Django messages without hiding collector or database failures."""
        from django.core.checks import CRITICAL, DEBUG, ERROR, INFO, WARNING

        severity = {
            DEBUG: _("Debug"),
            INFO: _("Info"),
            WARNING: _("Warning"),
            ERROR: _("Error"),
            CRITICAL: _("Critical"),
        }
        return [
            {
                "id": message.id,
                "severity": severity.get(message.level, str(message.level)),
                "message": message.msg,
                "hint": message.hint,
            }
            for message in messages
            if not message.is_silenced()
        ]

    def get_manage_checks(self, viewset, user):
        """Describe only this ViewSet's checks, separately from global startup diagnostics."""
        from crud_views.checks import collect_ancestor_checks, collect_conditional_checks, collect_viewset_icon_checks

        checks = list(viewset.checks())
        messages = [message for check in checks for message in check.messages()]
        messages += collect_ancestor_checks([viewset])
        messages += collect_conditional_checks([viewset])
        messages += collect_viewset_icon_checks([viewset])
        return {"count": len(checks), "messages": self._manage_check_messages(messages)}

    def get_context_data(self, **kwargs):
        # nested: the permission rows and holder diagnostics read auth records, which must be on default (06.18)
        _check_nested_auth(self, actor=self.request.user, model=self.cv_viewset.model)
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "cv": self.cv_viewset,
                "data": SimpleLazyObject(self._get_permission_data),
                "views": SimpleLazyObject(self.get_view_data),
                "permission_holders": SimpleLazyObject(self.get_permission_holders),
                "show_users": crud_views_settings.manage_show_users,
                "ancestor_policy": self.get_ancestor_policy_data(),
                "manage_permissions": self.get_manage_permissions(self.cv_viewset, self.request.user),
                "manage_views": self.get_manage_views(self.cv_viewset, self.request.user),
                "manage_checks": self.get_manage_checks(self.cv_viewset, self.request.user),
                "manage_facts": self.get_manage_facts(self.cv_viewset, self.request.user),
                "manage_hierarchy": self.get_manage_hierarchy(
                    self.cv_viewset, self.request.user, route_kwargs=self.kwargs
                ),
                "manage_routes": self.get_manage_routes(self.cv_viewset, self.request.user),
                "manage_ancestor_policy": self.get_manage_ancestor_policy(self.cv_viewset, self.request.user),
                "manage_docs_base_url": self.manage_docs_base_url,
            }
        )
        return context

    def get_ancestor_policy_data(self) -> dict:
        return self.get_manage_ancestor_policy(self.cv_viewset, None)

    def get_manage_ancestor_policy(self, viewset, user) -> dict:
        """The ViewSet's declared ancestor policy, for display (phase 06.18).

        Configuration only, not an authorization result: nothing is evaluated for the actor and no ancestor is
        loaded. The two scopes stay apart:

        * ``as_ancestor``: provider and ancestor fallback, used when this ViewSet is the ancestor of a nested
          request;
        * ``requests``: cascade, Read/Write pairs and exact action entries for nested requests that target this
          ViewSet. None at top level, where no ancestry applies.

        Each inheritable value shows the declared value (None = inherited) next to the effective one. Guardian's
        per-view ``cv_guardian_accept_global_perms`` is a separate, endpoint-local option (see GuardianManageView).
        """
        from crud_views.lib.ancestors import _READ, _WRITE, _effective_cascade, _effective_pair, _effective_provider

        policy = viewset.ancestor_policy

        def pair(value):
            return value.model_dump() if value is not None else None

        requests = None
        if viewset.parent is not None:
            requests = {
                "cascade": {"declared": policy.cascade, "effective": _effective_cascade(viewset)},
                "read": {"declared": pair(policy.read), "effective": pair(_effective_pair(viewset, _READ))},
                "write": {"declared": pair(policy.write), "effective": pair(_effective_pair(viewset, _WRITE))},
                "actions": {key: pair(value) for key, value in policy.actions.items()},
            }
        return {
            "as_ancestor": {
                "provider": policy.provider,
                "effective_provider": _effective_provider(viewset),
                "accept_global_perms": policy.accept_global_perms,
            },
            "requests": requests,
        }

    def get_view_data(self):
        return self._get_view_data(self.cv_viewset)

    @staticmethod
    def _get_view_data(viewset):
        data = OrderedDict()
        for key, view in viewset.get_all_views().items():
            view_data = OrderedDict(
                {
                    "base": OrderedDict(
                        {
                            "class": f"{view.__module__}.{view.__qualname__}",
                            "cv_key": view.cv_key,
                            "cv_path": view.cv_path,
                            "cv_backend_only": view.cv_backend_only,
                            "cv_list_actions": view.cv_list_actions,
                            "cv_list_action_method": view.cv_list_action_method,
                            "cv_context_actions": view.cv_context_actions,
                            "cv_home_key": view.cv_home_key,
                            "cv_success_key": view.cv_success_key,
                            "cv_success_keys": view.cv_success_keys,
                            "cv_cancel_key": view.cv_cancel_key,
                            "cv_cancel_keys": view.cv_cancel_keys,
                        }
                    ),
                    "templates": OrderedDict(
                        {
                            "cv_header_template": view.cv_header_template,
                            "cv_header_template_code": view.cv_header_template_code,
                            "cv_paragraph_template": view.cv_paragraph_template,
                            "cv_paragraph_template_code": view.cv_paragraph_template_code,
                            "cv_action_label_template": view.cv_action_label_template,
                            "cv_action_label_template_code": view.cv_action_label_template_code,
                            "cv_action_short_label_template": view.cv_action_short_label_template,
                            "cv_action_short_label_template_code": view.cv_action_short_label_template_code,
                        }
                    ),
                    "icons": OrderedDict(
                        {
                            "cv_icon_action": view.cv_icon_action,
                            "cv_icon_header": view.cv_icon_header,
                        }
                    ),
                }
            )
            data[key] = view_data
        return data
