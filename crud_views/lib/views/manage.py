from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ViewSetView


class ManageView(PermissionRequiredMixin, ViewSetView, generic.TemplateView):
    template_name = "crud_views/view_manage.html"

    vs_pk: bool = False  # does not need primary key
    vs_key = "manage"
    vs_path = "manage"
    vs_object = False

    vs_context_actions = crud_views_settings.manage_context_actions

    # texts and labels
    vs_header_template: str = crud_views_settings.manage_header_template
    vs_header_template_code: str = crud_views_settings.manage_header_template_code
    vs_paragraph_template: str = crud_views_settings.manage_paragraph_template
    vs_paragraph_template_code: str = crud_views_settings.manage_paragraph_template_code
    vs_action_label_template: str = crud_views_settings.manage_action_label_template
    vs_action_label_template_code: str = crud_views_settings.manage_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.manage_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.manage_action_short_label_template_code

    vs_icon_action = "fa-solid fa-gear"
    vs_icon_header = "fa-solid fa-gear"

    def has_permission(self):
        """
        Currently manage views are only attached to ViewSets via a global switch in settings
        """
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        permissions = self.vs.permissions
        rows = []
        for short, long in permissions.items():
            rows.append(dict(
                viewset=short,
                django=long,
                has_permission=self.request.user.has_perm(long)
            ))
        views = self.get_view_data()
        context.update({
            "vs": self.vs,
            "data": rows,
            "views": views
        })
        return context

    def get_view_data(self):
        data = OrderedDict()
        for key, view in self.vs.get_all_views().items():
            view_data = OrderedDict({
                "base": OrderedDict({
                    "class": str(view.__class__),
                    "vs_key": view.vs_key,
                    "vs_path": view.vs_path,
                    "vs_backend_only": view.vs_backend_only,
                    "vs_list_actions": view.vs_list_actions,
                    "vs_list_action_method": view.vs_list_action_method,
                    "vs_context_actions": view.vs_context_actions,
                    "vs_home_key": view.vs_home_key,
                    "vs_success_key": view.vs_success_key,
                    "vs_cancel_key": view.vs_cancel_key,
                    "vs_parent_key": view.vs_parent_key,
                }),
                "templates": OrderedDict({
                    "vs_header_template": view.vs_header_template,
                    "vs_header_template_code": view.vs_header_template_code,
                    "vs_paragraph_template": view.vs_paragraph_template,
                    "vs_paragraph_template_code": view.vs_paragraph_template_code,
                    "vs_action_label_template": view.vs_action_label_template,
                    "vs_action_label_template_code": view.vs_action_label_template_code,
                    "vs_action_short_label_template": view.vs_action_short_label_template,
                    "vs_action_short_label_template_code": view.vs_action_short_label_template_code,
                }),
                "icons": OrderedDict({
                    "vs_icon_action": view.vs_icon_action,
                    "vs_icon_header": view.vs_icon_header,
                }),
            })
            data[key] = view_data
        return data
