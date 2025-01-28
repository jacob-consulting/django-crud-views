from django import forms
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.polymorphic_views.utils import get_polymorphic_child_models_content_types


class PolymorphicContentTypeForm(forms.Form):
    polymorphic_ctype_id = forms.ChoiceField(label="Type", choices=[])

    def __init__(self, *args, polymorphic_ctype_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["polymorphic_ctype_id"].choices = polymorphic_ctype_choices


class PolymorphicCreateSelectView(ViewSetView, generic.FormView):
    template_name = "crud_views/view_create.html"
    form_class = PolymorphicContentTypeForm

    vs_key = "create_select"
    vs_object = False
    vs_path = "create/select"
    vs_success_key = "list"
    vs_context_actions = crud_views_settings.create_context_actions

    # texts and labels
    vs_header_template: str = crud_views_settings.create_select_header_template
    vs_header_template_code: str = crud_views_settings.create_select_header_template_code
    vs_paragraph_template: str = crud_views_settings.create_select_paragraph_template
    vs_paragraph_template_code: str = crud_views_settings.create_select_paragraph_template_code
    vs_action_label_template: str = crud_views_settings.create_select_action_label_template
    vs_action_label_template_code: str = crud_views_settings.create_select_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.create_select_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.create_select_action_short_label_template_code

    vs_icon_action = "fa-regular fa-square-plus"

    def get_form(self, form_class=None):
        form_class = form_class if form_class else self.get_form_class()
        content_types = get_polymorphic_child_models_content_types(self.model)
        polymorphic_ctype_choices = [(ct.id, ct.name) for ct in content_types.values()]
        form_kwargs = self.get_form_kwargs()
        form = form_class(polymorphic_ctype_choices=polymorphic_ctype_choices, **form_kwargs)
        return form

    def form_valid(self, form):
        polymorphic_ctype_id = form.cleaned_data["polymorphic_ctype_id"]
        kwargs = {"polymorphic_ctype_id": polymorphic_ctype_id}
        url = self.vs_get_url("create", extra_kwargs=kwargs)
        return HttpResponseRedirect(url)

    # def form_valid(self, form):
    #     """
    #     Set parent model instance at form instance
    #     """
    #
    #     parent_model = self.vs.get_parent_model()
    #     if parent_model:
    #         attr = self.vs.get_parent_attributes(first_only=True)
    #         arg = self.vs.get_parent_url_args(first_only=True)
    #         pk = self.kwargs[arg]
    #         parent = get_object_or_404(parent_model, pk=pk)
    #         setattr(form.instance, attr, parent)
    #
    #     return super().form_valid(form)


class PolymorphicCreateSelectViewPermissionRequired(ViewSetViewPermissionRequiredMixin,
                                                    PolymorphicCreateSelectView):
    vs_permission = "add"
