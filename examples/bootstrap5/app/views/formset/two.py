from crispy_forms.helper import FormHelper
from crispy_forms.layout import Row
from django.forms import modelform_factory

from app.models.poly import PolyTwo
from crud_views.lib.crispy import Column6
from crud_views.lib.crispy.form import CrispyForm

from crud_views.lib.formsets import Formsets

_PolyTwoForm = modelform_factory(
    PolyTwo,
    fields=[
        "shared",
        "two",
    ],
)


class PolyTwoForm(CrispyForm, _PolyTwoForm):

    def get_layout_fields(self):
        return [
            Row(Column6("shared"), Column6("two")),
            Row(Formsets())
        ]

    @property
    def helper(self) -> FormHelper:
        # todo: is this needed?
        h = super().helper
        h.form_tag = False
        return h
