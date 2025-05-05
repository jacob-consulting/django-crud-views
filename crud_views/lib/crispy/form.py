from typing import List

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Layout, Row, Submit, LayoutObject, BaseInput
from django.forms import ModelForm, Form, BooleanField
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column4


class CrispyFormMixin:
    """
    CrispyForm helps to application DRY:

        class FooForm(CrispyModelForm):
            class Meta:
                model = Foo
                fields = ["foo", "bar"]

            def get_layout_fields(self) -> LayoutObject | BaseInput | List[LayoutObject | BaseInput]:
                return [
                    Row(
                        Column6("foo"), Column6("bar"),
                    )
                ]

    The for has FormActions element with two buttons:
        - save
        - cancel, which is linked to the cancel key defined the CrudView

    The mixin for CrudView(s) adds the view context cv_view to the form. CrispyModelViewMixin,
    when added to a CrudView, sets this extra argument for the form in get_form_kwargs.
    """

    submit_label: str = _("Save")

    def __init__(self, cv_view, *args, **kwargs):
        self.cv_view = cv_view
        super().__init__(*args, **kwargs)

    @property
    def helper(self) -> FormHelper:
        helper = FormHelper()
        fields = self.get_layout_fields()
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        helper.layout = Layout(
            *fields,
            self.get_form_actions()
        )
        return helper

    def get_layout_fields(self) -> LayoutObject | BaseInput | List[LayoutObject | BaseInput]:
        raise NotImplementedError

    def get_form_actions(self) -> FormActions:
        return FormActions(
            self.get_submit_button(),
            self.get_cancel_button()
        )

    def get_submit_button_kwargs(self) -> dict:
        return {
            "name": "submit",
            "value": self.submit_label
        }

    def get_submit_button(self) -> Submit:
        """
        Submit button for FormActions
        """
        return Submit(**self.get_submit_button_kwargs())

    def get_cancel_button_kwargs(self) -> dict:
        request = self.cv_view.request
        # get the object from the form instance or the view context object
        obj = getattr(self, "instance", getattr(self.cv_view, "object", None))
        context = self.cv_view.get_cancel_button_context(obj=obj, user=request.user, request=request)
        url = context["cv_url"]
        onclick = f"location.href='{url}';return false;"
        return {
            "name": "reset",
            "value": context["cv_action_label"],
            "onclick": onclick,
            "css_class": "btn btn-secondary"
        }

    def get_cancel_button(self) -> Button:
        return Button(**self.get_cancel_button_kwargs())


class CrispyModelForm(CrispyFormMixin, ModelForm):
    """
    Base class for ModelForm with crispy forms.
    This form takes the current viewset view as an argument and uses it to generate the cancel button.
    """
    pass


class CrispyForm(CrispyFormMixin, Form):
    """
    Base class for Form with crispy forms.
    This form takes the current viewset view as an argument and uses it to generate the cancel button.
    """
    pass


class CrispyDeleteForm(CrispyForm):
    """
    Default delete from with confirmation
    """
    confirm = BooleanField(label=_("Confirm deletion"))

    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Row(
                Column4("confirm")
            ),
            FormActions(
                Submit("delete", "Delete"),
                self.get_cancel_button(),
            )
        )
        return helper


class CrispyViewMixin:
    """
    This mixin makes sure that CrispyModelForm gets the cv_view argument
    """

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()  # noqa
        form_class = self.get_form_class()  # noqa
        if issubclass(form_class, (CrispyModelForm, CrispyForm)):
            kwargs["cv_view"] = self
        return kwargs


# todo: remove this
class CrispyModelViewMixin(CrispyViewMixin):
    pass
