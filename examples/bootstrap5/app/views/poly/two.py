from crispy_forms.layout import Row
from django.forms import modelform_factory

from app.models import PolyTwo
from crud_views.lib.crispy import Column6
from crud_views.lib.crispy.form import CrispyForm

_PolyTwoForm = modelform_factory(
    PolyTwo,
    fields=[
        "shared",
        "two",
    ],
)


class PolyTwoForm(CrispyForm, _PolyTwoForm):

    def get_layout_fields(self):
        return Row(Column6("shared"), Column6("two")),
