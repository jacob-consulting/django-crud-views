from django.views.generic.base import TemplateResponseMixin, View

from crud_views.lib.views.mixins import CrudViewProcessFormMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class CustomFormView(CrudViewProcessFormMixin, CrudView,
                     FormMixin,
                     DetailView):
    """
    Object based view with custom form.
    Note: you have to set:
        - cv_key
        - cv_path
    """
    template_name = "crud_views/view_custom_form.html"
    cv_context_actions = crud_views_settings.detail_context_actions

    def cv_form_valid(self, context: dict):
        """
        Handle valid form
        """
        pass

    def cv_form_valid_hook(self, context: dict):
        """
        Handle valid form hook
        """
        pass


class CustomFormViewPermissionRequired(CrudViewPermissionRequiredMixin, CustomFormView):  # this file
    cv_permission = "view"


class CustomFormNoObjectView(CrudViewProcessFormMixin, CrudView,
                             FormMixin,
                             TemplateResponseMixin,
                             View):
    """
    Non object based view with custom form.
    Note: you have to set:
        - cv_key
        - cv_path
    """
    template_name = "crud_views/view_custom_form.html"
    cv_context_actions = crud_views_settings.detail_context_actions

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def cv_form_valid(self, context: dict):
        """
        Handle valid form
        """
        pass

    def cv_form_valid_hook(self, context: dict):
        """
        Handle valid form hook
        """
        pass


class CustomFormNoObjectViewPermissionRequired(CrudViewPermissionRequiredMixin, CustomFormNoObjectView):  # this file
    cv_permission = "view"
