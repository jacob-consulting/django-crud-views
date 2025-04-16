from __future__ import annotations

from typing import List

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, LayoutObject, Field, BaseInput
from crud_views.lib.crispy import Column4, Column2
from django.core.exceptions import ValidationError
from django.forms import BaseForm
from django.forms.models import BaseInlineFormSet, ModelForm

from .formsets import FormSet
from .layout import FormControl


class InlineFormSet(BaseInlineFormSet):
    def __init__(
            self,
            formset: FormSet,
            parent_form: BaseForm | None = None,
            data=None,
            files=None,
            instance=None,
            save_as_new=False,
            prefix=None,
            queryset=None,
            **kwargs,
    ):
        self.formset = formset
        self.parent_form = parent_form
        super().__init__(data=data,
                         files=files,
                         instance=instance,
                         save_as_new=save_as_new,
                         prefix=prefix,
                         queryset=queryset,
                         **kwargs)

    def __str__(self):
        parent = self.formset.parent.key if self.formset.parent else None
        num_forms = len(self.forms)
        return f"InlineFormSet({self.prefix},#{num_forms},m={self.form.Meta.model},p={parent})"

    __repr__ = __str__

    @property
    def helper(self) -> FormHelper:
        return self.get_helper()

    def get_helper(self) -> FormHelper:
        helper = FormHelper()
        helper.form_tag = False
        helper.disable_csrf = True
        helper.render_hidden_fields = True  # IMPORTANT: crispy needs this to render hidden fields
        helper.form_show_labels = False  # todo: get this from formset config

        fields = self.get_helper_layout_fields()
        assert isinstance(fields, list)

        hidden = self.get_helper_hidden_fields()
        assert isinstance(hidden, list)

        all_fields = fields + hidden
        helper.layout = Layout(*all_fields)
        return helper

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        raise NotImplementedError()

    def get_helper_hidden_fields(self) -> List[LayoutObject]:
        fields = []
        if self.formset.can_order:
            fields.append(Field("ORDER", type="hidden"))
        if self.formset.can_delete:
            fields.append(Field("DELETE", type="hidden"))
        return fields

    @property
    def form_control(self):
        return FormControl(formset=self.formset)

    @property
    def form_control_col4(self) -> LayoutObject:
        return Column4(self.form_control, css_class="text-end")

    @property
    def form_control_col2(self) -> LayoutObject:
        return Column2(self.form_control, css_class="text-end")

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["cv_view"] = self.formset.cv_view
        return kwargs

    @property
    def has_any_form_with_data(self) -> bool:
        for data in self.cleaned_data:
            if len(data) and data.get("DELETE") is not True:
                return True
        return False

    @staticmethod
    def is_empty_form(form) -> bool:
        if form.is_valid() and not form.cleaned_data:
            return True
        else:
            # Either the form has errors (isn't valid) or
            # it doesn't have errors and contains data.
            return False

    def clean(self):
        super().clean()
        if self.parent_form:
            if self.has_any_form_with_data:
                if self.is_empty_form(self.parent_form):
                    self.parent_form.add_error(
                        field=None,
                        error="Child TODO requires at least one TODO set"
                    )
                    raise ValidationError("Parent form is required")


class CrispyInlineFormMixin:
    """
    This is needed for polymorphic inline formsets.
    """

    @property
    def helper(self) -> FormHelper:
        helper = FormHelper()
        helper.form_tag = False
        helper.disable_csrf = True
        helper.render_hidden_fields = True  # IMPORTANT: crispy needs this to render hidden fields
        helper.form_show_labels = True  # todo: get this from formset config
        fields = self.get_layout_fields()
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        helper.layout = Layout(*fields)
        return helper

    def get_layout_fields(self) -> LayoutObject | BaseInput | List[LayoutObject | BaseInput]:
        raise NotImplementedError


class CrispyInlineModelForm(CrispyInlineFormMixin, ModelForm):
    """
    This is needed for polymorphic inline formsets.
    """
    pass
