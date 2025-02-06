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
    cv_icon_action = "fa-solid fa-gear"
    cv_icon_header = "fa-solid fa-gear"

    def has_permission(self):
        """
        Currently manage views are only attached to ViewSets via a global switch in settings
        """
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        permissions = self.cv_viewset.permissions
        rows = []
        for short, long in permissions.items():
            rows.append(dict(
                viewset=short,
                django=long,
                has_permission=self.request.user.has_perm(long)
            ))
        views = self.get_view_data()
        context.update({
            "cv": self.cv_viewset,
            "data": rows,
            "views": views
        })
        return context

    def get_view_data(self):
        data = OrderedDict()
        for key, view in self.cv_viewset.get_all_views().items():
            view_data = OrderedDict({
                "base": OrderedDict({
                    "class": str(view.__class__),
                    "cv_key": view.cv_key,
                    "cv_path": view.cv_path,
                    "cv_backend_only": view.cv_backend_only,
                    "cv_list_actions": view.cv_list_actions,
                    "cv_list_action_method": view.cv_list_action_method,
                    "cv_context_actions": view.cv_context_actions,
                    "cv_home_key": view.cv_home_key,
                    "cv_success_key": view.cv_success_key,
                    "cv_cancel_key": view.cv_cancel_key,
                    "cv_parent_key": view.cv_parent_key,
                }),
                "templates": OrderedDict({
                    "cv_header_template": view.cv_header_template,
                    "cv_header_template_code": view.cv_header_template_code,
                    "cv_paragraph_template": view.cv_paragraph_template,
                    "cv_paragraph_template_code": view.cv_paragraph_template_code,
                    "cv_action_label_template": view.cv_action_label_template,
                    "cv_action_label_template_code": view.cv_action_label_template_code,
                    "cv_action_short_label_template": view.cv_action_short_label_template,
                    "cv_action_short_label_template_code": view.cv_action_short_label_template_code,
                }),
                "icons": OrderedDict({
                    "cv_icon_action": view.cv_icon_action,
                    "cv_icon_header": view.cv_icon_header,
                }),
            })
            data[key] = view_data
        return data
