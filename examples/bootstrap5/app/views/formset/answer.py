from crispy_forms.layout import Row
from crud_views.lib.crispy import Column4, Column8
from polymorphic.formsets import polymorphic_inlineformset_factory, PolymorphicFormSetChild, \
    BasePolymorphicInlineFormSet

from app.models.poly import Poly, PolyAnswer, PolyAnswerText, PolyAnswerNumber
from crud_views.lib.formsets.inline_formset import CrispyInlineModelForm


class PolyAnswerTextForm(CrispyInlineModelForm):
    class Meta:
        model = PolyAnswerText
        fields = ["answer", "text"]

    def get_layout_fields(self):
        return Row(Column4("answer"), Column8("text"))  # , "id"


PolyAnswerTextFormSetChild = PolymorphicFormSetChild(
    PolyAnswerText,
    form=PolyAnswerTextForm,
    fields=None,
    exclude=None,
    formfield_callback=None,
    widgets=None,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None)


class PolyAnswerNumberForm(CrispyInlineModelForm):
    class Meta:
        model = PolyAnswerNumber
        fields = [
            # "id",
            "answer", "number"
        ]

    def get_layout_fields(self):
        return Row(Column8("answer"), Column4("number"))  # , "id"


PolyAnswerNumberFormSetChild = PolymorphicFormSetChild(
    PolyAnswerNumber,
    form=PolyAnswerNumberForm,
    fields=None,
    exclude=None,
    formfield_callback=None,
    widgets=None,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None)


# todo: move this to module
class PolymorphicInlineFormSet(BasePolymorphicInlineFormSet):
    def __init__(self, formset, parent_form, *args, **kwargs):
        self.formset = formset
        self.parent_form = parent_form
        super().__init__(*args, **kwargs)


PolyAnswerFormSet = polymorphic_inlineformset_factory(
    parent_model=Poly,
    model=PolyAnswer,
    formset=PolymorphicInlineFormSet,
    formset_children=[
        PolyAnswerTextFormSetChild,
        PolyAnswerNumberFormSetChild
    ],
    fields="__all__",
    extra=0,    # polymorphic inlines cannot be created currently
    can_delete=False,
    can_order=False,
)
