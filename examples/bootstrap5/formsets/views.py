from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory

from crud_views.lib.crispy import Column8, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

from formsets.models import Choice, Question, Questionnaire

cv_questionnaire = ViewSet(model=Questionnaire, name="questionnaire", icon_header="fa-solid fa-list-check")


class QuestionnaireForm(CrispyModelForm):
    class Meta:
        model = Questionnaire
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]

    @property
    def helper(self) -> FormHelper:
        # the formsets render their own form tags
        h = super().helper
        h.form_tag = False
        return h


class QuestionForm(CrispyModelForm):
    class Meta:
        model = Question
        fields = ["text"]


class QuestionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("text"), self.form_control_col4)]


QuestionFormSet = inlineformset_factory(
    Questionnaire,
    Question,
    formset=QuestionInlineFormSet,
    form=QuestionForm,
    fields=["text"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)


class ChoiceForm(CrispyModelForm):
    class Meta:
        model = Choice
        fields = ["label"]


class ChoiceInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("label"), self.form_control_col4)]


ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    formset=ChoiceInlineFormSet,
    form=ChoiceForm,
    fields=["label"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)


cv_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        questions=FormSet(
            title="Questions",
            klass=QuestionFormSet,
            fields=["text"],
            pk_field="id",
            children=OrderedDict(
                choices=FormSet(
                    title="Choices",
                    klass=ChoiceFormSet,
                    fields=["label"],
                    pk_field="id",
                )
            ),
        ),
    )
)


class QuestionnaireTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class QuestionnaireListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_questionnaire
    table_class = QuestionnaireTable


class QuestionnaireDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_questionnaire
    cv_property_display = [
        {
            "title": "Questionnaire",
            "icon": "list-check",
            "properties": ["id", "title", {"path": "question_count", "detail": "Number of questions"}],
        },
    ]

    def question_count(self, instance):
        return instance.questions.count()


class QuestionnaireCreateView(CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_message = "Created questionnaire »{object}«"


class QuestionnaireUpdateView(CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_message = "Updated questionnaire »{object}«"


class QuestionnaireDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_questionnaire
    form_class = CrispyDeleteForm
    cv_message = "Deleted questionnaire »{object}«"
