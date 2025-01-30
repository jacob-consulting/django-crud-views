from typing import List, Iterable, Any

from django.core.checks import CheckMessage, Error
from django.views import generic
from django_filters.conf import is_callable

from crud_views.lib.check import Check
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin


class PropertyCheck(Check):
    """
    Check for detail properties
    """

    @property
    def fields(self) -> dict:
        return {
            field.attname if hasattr(field, "attname") else field.get_accessor_name(): field
            for field in self.context.model._meta.get_fields()  # noqa
        }

    def messages(self) -> Iterable[CheckMessage]:
        fields = self.fields
        for prop in self.context.cv_properties:  # noqa
            is_model_prop = prop in fields
            cv_prop = getattr(self.context, prop, None)
            is_cv_prop = getattr(cv_prop, "cv_property", False)
            if not is_model_prop and not is_cv_prop:
                yield Error(id=f"viewset.{self.id}", msg=f"{self.msg} at {self.context}: {prop}")


class DetailView(ViewSetView, generic.DetailView):
    template_name = "crud_views/view_detail.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions
    cv_properties: List[str] = []

    # texts and labels
    cv_header_template: str = crud_views_settings.detail_header_template
    cv_header_template_code: str = crud_views_settings.detail_header_template_code
    cv_paragraph_template: str = crud_views_settings.detail_paragraph_template
    cv_paragraph_template_code: str = crud_views_settings.detail_paragraph_template_code
    cv_action_label_template: str = crud_views_settings.detail_action_label_template
    cv_action_label_template_code: str = crud_views_settings.detail_action_label_template_code
    cv_action_short_label_template: str = crud_views_settings.detail_action_short_label_template
    cv_action_short_label_template_code: str = crud_views_settings.detail_action_short_label_template_code

    cv_icon_action = "fa-regular fa-eye"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield PropertyCheck(context=cls, id="E300", attribute="attribute")   # todo

    def cv_get_property(self, obj: object, property: str) -> Any:
        p = getattr(self, property, None)
        if p:
            if not is_callable(p):
                raise ViewSetError(f"{property} is not callable at {obj}")
            return p()
        else:
            p = getattr(obj, property)
            return p


class DetailViewPermissionRequired(ViewSetViewPermissionRequiredMixin, DetailView):  # this file
    cv_permission = "view"
