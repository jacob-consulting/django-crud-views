from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

from crud_views.lib.ancestor_db import _check_nested_auth
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView


class ManageView(PermissionRequiredMixin, CrudView, generic.TemplateView):
    template_name = "crud_views/view_manage.html"

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

    def get_context_data(self, **kwargs):
        # nested: the permission rows and holder diagnostics read auth records, which must be on default (06.18)
        _check_nested_auth(self, actor=self.request.user, model=self.cv_viewset.model)
        context = super().get_context_data(**kwargs)
        permissions = self.cv_viewset.permissions
        rows = []
        for short, long in permissions.items():
            rows.append({"viewset": short, "django": long, "has_permission": self.request.user.has_perm(long)})
        views = self.get_view_data()
        permission_holders = self.get_permission_holders()
        context.update(
            {
                "cv": self.cv_viewset,
                "data": rows,
                "views": views,
                "permission_holders": permission_holders,
                "show_users": crud_views_settings.manage_show_users,
                "ancestor_policy": self.get_ancestor_policy_data(),
            }
        )
        return context

    def get_ancestor_policy_data(self) -> dict:
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

        viewset = self.cv_viewset
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
        data = OrderedDict()
        for key, view in self.cv_viewset.get_all_views().items():
            view_data = OrderedDict(
                {
                    "base": OrderedDict(
                        {
                            "class": str(view.__class__),
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
