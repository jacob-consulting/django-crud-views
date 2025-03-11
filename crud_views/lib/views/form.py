from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class CustomFormView(CrudView, FormMixin, DetailView):
    """
    Object based view with custom form.
    Note: you have to set:
        - cv_key
        - cv_path
    """
    template_name = "crud_views/view.custom_form.html"
    cv_context_actions = crud_views_settings.detail_context_actions

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class CustomFormViewPermissionRequired(CrudViewPermissionRequiredMixin, CustomFormView):  # this file
    cv_permission = "view"
