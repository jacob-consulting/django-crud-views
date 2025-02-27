import inspect
from typing import List, Dict, Tuple, Any

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.db.models import Field, ManyToManyField
from django.db.models.fields import BooleanField
from django.forms import Form, Widget
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DetailWidget(Widget):
    template_name = "crud_views/detail/widgets/display.html"

    def format_value(self, value):
        """
        Return a value as it should appear when rendered in a template.
        """
        return value


class BoolWidget(DetailWidget):
    template_name = "crud_views/detail/widgets/bool.html"


class DateWidget(DetailWidget):
    template_name = "crud_views/detail/widgets/date.html"


class DetailField(forms.Field):
    def __init__(self, *args, **kwargs):
        kwargs["required"] = False
        super().__init__(*args, **kwargs)


class DetailForm(Form):

    def __init__(self, layout: Layout, *args, **kwargs):
        self.layout = layout
        super().__init__(*args, **kwargs)

    @property
    def helper(self) -> FormHelper:
        helper = FormHelper()
        helper.layout = self.layout
        helper.field_template = "crud_views/detail/field.html"  # for testing only
        return helper


class DetailLayoutView(CrudView, generic.DetailView):
    template_name = "crud_views/view_detail_crispy.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions
    cv_properties: List[str] = []

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    # icons
    cv_icon_action = "fa-regular fa-eye"

    # todo: add system checks

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        form = self.cv_get_form()
        data["form"] = form
        return data

    @property
    def cv_layout(self) -> Layout:
        raise NotImplementedError

    @property
    def cv_layout_fields(self) -> List[str]:
        return [pointer.name for pointer in self.cv_layout.get_field_names()]

    def cv_get_model_fields(self) -> Tuple[Dict[str, Field], Dict[str, Any]]:
        """
        Todo
        """
        layout_fields = self.cv_layout_fields

        fields, initial = dict(), dict()
        for model_field in self.model._meta.get_fields():
            if model_field.name not in layout_fields:
                continue

            #if

            if isinstance(model_field, ManyToManyField):
                value = "M2N"
            else:
                value = getattr(self.object, model_field.name)

            if isinstance(model_field, BooleanField):
                widget = BoolWidget
            else:
                widget = DetailWidget

            field = DetailField(label=model_field.verbose_name, widget=widget)
            initial[model_field.name] = value
            fields[model_field.name] = field

        return fields, initial

    def cv_get_property_fields(self) -> Tuple[Dict[str, Field], Dict[str, Any]]:
        """
        Get dictionary of view properties
        """
        layout_fields = self.cv_layout_fields

        fields, initial = dict(), dict()
        for key, member in inspect.getmembers(self):

            if key not in layout_fields:
                continue

            if getattr(member, "cv_property", False) is False:
                continue

            property_type = member.cv_type
            label = member.cv_label or key.capitalize()

            if property_type is str:
                widget = DetailWidget
            elif property_type is bool:
                widget = BoolWidget
            else:
                raise

            field = DetailField(label=label, widget=widget)
            fields[key] = field
            initial[key] = getattr(self, key)()

        return fields, initial

    def cv_get_form(self) -> Form:

        # Define the fields for the Meta class
        meta_fields = {
            'fields': self.cv_layout_fields
        }

        # Create a Meta class dynamically
        Meta = type('Meta', (object,), meta_fields)

        # Define attributes for the new form class
        attrs = {'Meta': Meta}

        #
        model_fields, model_initial = self.cv_get_model_fields()
        properties_fields, property_initial = self.cv_get_property_fields()

        # todo: warn if fields collide

        fields, initial = dict(), dict()

        fields.update(model_fields)
        fields.update(properties_fields)


        initial.update(model_initial)
        initial.update(property_initial)

        for key, field in fields.items():
            attrs[key] = field

        klass = type('DynamicDetailForm', (DetailForm,), attrs)
        form = klass(layout=self.cv_layout, initial=initial)

        return form


class DetailLayoutViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailLayoutView):  # this file
    cv_permission = "view"
