from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

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
        # Nested manage: ancestry first (phase 06.18), then the unchanged local settings/group gate that
        # PermissionRequiredMixin.dispatch runs through has_permission().
        response = self._cv_ancestor_guard()
        if response is not None:
            return response
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _cv_manage_public() -> bool:
        """The settings make manage pages public ("yes", or "debug_only" with DEBUG on)."""
        if crud_views_settings.manage_views_enabled == "yes":
            return True
        from django.conf import settings as django_settings

        return crud_views_settings.manage_views_enabled == "debug_only" and django_settings.DEBUG

    def _cv_ancestor_actor_response(self, *, protected: bool):
        """Actor admission of a nested manage request, before any ancestor lookup.

        Protected ancestry: the shared actor rule (anonymous → login, inactive → 403), even when the settings
        make manage public. All-none ancestry: the manage gate's actual early rule — public settings admit
        everybody, otherwise an anonymous actor is denied; group membership stays a local gate after ancestry."""
        if protected:
            from crud_views.lib.ancestors import _protected_actor_response

            return _protected_actor_response(self)
        if self._cv_manage_public() or self.request.user.is_authenticated:
            return None
        return self.handle_no_permission()

    def has_permission(self):
        if self._cv_manage_public():
            return True
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.groups.filter(name=crud_views_settings.manage_group).exists()

    def get_permission_holders(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

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
            }
        )
        return context

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
