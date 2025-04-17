from collections import OrderedDict
from typing import List

import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Row, LayoutObject
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm, Column8
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, \
    CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.views.detail import PropertyGroup
from crud_views.lib.viewset import ViewSet
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext as _

from app.models.questions import Question, QuestionChoice, QuestionTag, QuestionChoiceTag, QuestionChoiceTagAnnotation
from crud_views.lib.formsets import FormSets, FormSet, FormSetMixin, InlineFormSet, Formsets

cv_question = ViewSet(
    model=Question,
    name="question",
    icon_header="fa-solid fa-question"
)

EXTRA = 1


class QuestionForm(CrispyModelForm):
    class Meta:
        model = Question
        fields = ["question"]

    def get_layout_fields(self):
        return [
            Row(Column4("question")),
            Formsets()
        ]

    @property
    def helper(self) -> FormHelper:
        # todo: is this needed?
        h = super().helper
        h.form_tag = False
        return h


class QuestionTable(Table):
    id = LinkDetailColumn()
    question = tables.Column()


class QuestionListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Question
    table_class = QuestionTable
    cv_viewset = cv_question


class QuestionDetailView(DetailViewPermissionRequired):
    model = Question
    cv_viewset = cv_question


    cv_property_groups = [
        PropertyGroup(
            key="properties",
            label=_("Properties"),
            properties=[
                "id",
                "question",
            ]
        ),
    ]


class QuestionChoiceForm(CrispyModelForm):
    class Meta:
        model = QuestionChoice
        fields = [
            "choice", "help_text",
        ]


class ChoiceInlineFormSet(InlineFormSet):

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [
            Row(
                Column4("choice"), Column4("help_text"),
                self.form_control_col4
            )
        ]


ChoiceFormSet = inlineformset_factory(
    Question,
    QuestionChoice,
    formset=ChoiceInlineFormSet,
    form=QuestionChoiceForm,
    fields=[
        "choice", "help_text",  # "order",
    ],
    extra=EXTRA,
    # this adds fields to the form
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)


class QuestionTagForm(CrispyModelForm):
    class Meta:
        model = QuestionTag
        fields = ["tag"]


class QuestionTagInlineFormSet(InlineFormSet):

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [
            Row(
                Column8("tag"),
                self.form_control_col4
            )
        ]


QuestionTagFormSet = inlineformset_factory(
    Question,
    QuestionTag,
    formset=QuestionTagInlineFormSet,
    form=QuestionTagForm,
    fields=["tag"],
    extra=EXTRA,
    # this adds fields to the form
    can_delete=True,
    can_delete_extra=True,
    can_order=False,
)


class QuestionChoiceTagForm(CrispyModelForm):
    class Meta:
        model = QuestionChoiceTag
        fields = ["tag", ]


class QuestionChoiceTagInlineFormSet(InlineFormSet):

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [
            Row(
                Column8("tag"),
                self.form_control_col4
            )
        ]


QuestionChoiceTagFormSet = inlineformset_factory(
    QuestionChoice,
    QuestionChoiceTag,
    formset=QuestionChoiceTagInlineFormSet,
    form=QuestionChoiceTagForm,
    fields=["tag"],
    extra=2,  # EXTRA,
    # this adds fields to the form
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)


class QuestionChoiceTagAnnotationInlineFormSet(InlineFormSet):

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [
            Row(
                Column8("annotation"),
                self.form_control_col4
            )
        ]


QuestionChoiceTagAnnotationFormSet = inlineformset_factory(
    QuestionChoiceTag,
    QuestionChoiceTagAnnotation,
    formset=QuestionChoiceTagAnnotationInlineFormSet,
    form=QuestionChoiceTagForm,
    fields=["annotation"],
    extra=EXTRA,
    # this adds fields to the form
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)

cv_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        choices=FormSet(  # noqa
            title=_("Choices"),
            klass=ChoiceFormSet,
            fields=["choice", "help_text"],
            pk_field="id",
            children=OrderedDict(
                tags=FormSet(
                    title=_("Tags"),
                    klass=QuestionChoiceTagFormSet,
                    fields=["tag"],
                    pk_field="id",
                    children=OrderedDict(
                        annotations=FormSet(
                            title=_("Annotations"),
                            klass=QuestionChoiceTagAnnotationFormSet,
                            fields=["annotation"],
                            pk_field="id",
                        )
                    )
                )
            )
        ),
        tags=FormSet(
            title=_("Tags"),
            klass=QuestionTagFormSet,
            fields=["tag"],
            pk_field="id",
        )
    )
)


class QuestionUpdateView(CrispyModelViewMixin, FormSetMixin, UpdateViewPermissionRequired):
    model = Question
    form_class = QuestionForm
    cv_viewset = cv_question
    cv_formsets: FormSets = cv_formsets


class QuestionCreateView(CrispyModelViewMixin, FormSetMixin, CreateViewPermissionRequired):
    model = Question
    form_class = QuestionForm
    cv_viewset = cv_question
    cv_formsets: FormSets = cv_formsets


class QuestionDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Question
    form_class = CrispyDeleteForm
    cv_viewset = cv_question
