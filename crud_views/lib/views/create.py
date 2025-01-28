from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin


class CreateView(ViewSetView, generic.CreateView):
    template_name = "crud_views/view_create.html"

    vs_key = "create"
    vs_object = False
    vs_path = "create"
    vs_success_key = "list"
    vs_context_actions = crud_views_settings.create_context_actions

    # texts and labels
    vs_header_template: str | None = crud_views_settings.create_header_template
    vs_header_template_code: str | None = crud_views_settings.create_header_template_code
    vs_paragraph_template: str | None = crud_views_settings.create_paragraph_template
    vs_paragraph_template_code: str | None = crud_views_settings.create_paragraph_template_code
    vs_action_label_template: str | None = crud_views_settings.create_action_label_template
    vs_action_label_template_code: str | None = crud_views_settings.create_action_label_template_code
    vs_action_short_label_template: str | None = crud_views_settings.create_action_short_label_template
    vs_action_short_label_template_code: str | None = crud_views_settings.create_action_short_label_template_code

    vs_message_template: str | None = crud_views_settings.create_message_template
    vs_message_template_code: str | None = crud_views_settings.create_message_template_code

    vs_icon_action = "fa-regular fa-square-plus"

    def form_valid(self, form):
        """
        Set parent model instance at form instance
        """

        parent_model = self.vs.get_parent_model()
        if parent_model:
            attr = self.vs.get_parent_attributes(first_only=True)
            arg = self.vs.get_parent_url_args(first_only=True)
            pk = self.kwargs[arg]
            parent = get_object_or_404(parent_model, pk=pk)
            setattr(form.instance, attr, parent)

        return super().form_valid(form)


class CreateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, CreateView):  # this file
    vs_permission = "add"
