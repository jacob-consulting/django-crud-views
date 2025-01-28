from crispy_forms.layout import Row
from django.forms import modelform_factory

from app.models import PolyOne
from crud_views.lib.crispy import Column6
from crud_views.lib.crispy.form import CrispyForm

_PolyOneForm = modelform_factory(
    PolyOne,
    fields=[
        "shared",
        "one",
    ],
)


class PolyOneForm(CrispyForm, _PolyOneForm):

    def get_layout_fields(self):
        return Row(Column6("shared"), Column6("one")),
