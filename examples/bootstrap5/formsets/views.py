from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column8, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import (
    CompactColumn,
    CompactLayout,
    FormSet,
    FormSetMixin,
    FormSets,
    Formsets,
    InlineFormSet,
)
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from formsets.models import Checklist, ChecklistItem, Choice, Question, Questionnaire

cv_questionnaire = ViewSet(model=Questionnaire, name="questionnaire", icon_header="fa-solid fa-list-check")


class QuestionnaireForm(CrispyModelForm):
    class Meta:
        model = Questionnaire
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]


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
            title=_("Questions"),
            klass=QuestionFormSet,
            fields=["text"],
            pk_field="id",
            children=OrderedDict(
                choices=FormSet(
                    title=_("Choices"),
                    row_legend=False,
                    klass=ChoiceFormSet,
                    fields=["label"],
                    pk_field="id",
                )
            ),
        ),
    )
)

# Compact rows use the column declaration instead of a duplicate crispy row layout.
CompactQuestionFormSet = inlineformset_factory(
    Questionnaire,
    Question,
    formset=InlineFormSet,
    form=QuestionForm,
    fields=["text"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)

CompactChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    formset=InlineFormSet,
    form=ChoiceForm,
    fields=["label"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)

cv_compact_formsets = FormSets(
    formsets=OrderedDict(
        questions=FormSet(
            title=_("Questions"),
            klass=CompactQuestionFormSet,
            fields=["text"],
            pk_field="id",
            compact_layout=CompactLayout(columns=[CompactColumn("text", span=8)], controls_span=4),
            children=OrderedDict(
                choices=FormSet(
                    title=_("Choices"),
                    klass=CompactChoiceFormSet,
                    fields=["label"],
                    pk_field="id",
                    compact_layout=CompactLayout(columns=[CompactColumn("label", span=8)], controls_span=4),
                )
            ),
        )
    )
)


class QuestionnaireTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class QuestionnaireListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_questionnaire
    table_class = QuestionnaireTable
    cv_context_actions = ["parent", "list", "filter", "create", "compact_create"]
    cv_context_actions_inline = []  # labelled menu keeps the comparison readable on narrow screens
    cv_list_actions = ["detail", "update", "compact_update", "delete"]
    cv_list_actions_label_mode = {"update": "label", "compact_update": "label"}
    cv_paragraph_template_code = _(
        'Try the <a href="{% url "checklist-list" %}">Checklist example</a> for compact rows with Done checkboxes.'
    )


class QuestionnaireDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_questionnaire
    cv_context_actions = ["home", "detail", "update", "compact_update", "delete"]
    cv_context_actions_inline = []
    cv_property_display = [
        {
            "title": _("Questionnaire"),
            "icon": "fas:list-check",
            "properties": ["id", "title", {"path": "question_count", "detail": _("Number of questions")}],
        },
    ]

    def question_count(self, instance):
        return instance.questions.count()


class QuestionnaireCreateView(
    BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_context_actions = ["home", "create", "compact_create"]
    cv_context_actions_inline = []
    cv_action_label_template_code = _("Create classic")
    cv_action_short_label_template_code = _("Create classic")
    cv_message_template_code = _("Created questionnaire “{{ object }}”")


class QuestionnaireUpdateView(
    BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired
):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_context_actions = ["home", "detail", "update", "compact_update", "delete"]
    cv_context_actions_inline = []
    cv_action_label_template_code = _("Edit classic")
    cv_action_short_label_template_code = _("Edit classic")
    cv_message_template_code = _("Updated questionnaire “{{ object }}”")


class QuestionnaireCompactCreateView(QuestionnaireCreateView):
    cv_viewset = cv_questionnaire
    cv_key = "compact_create"
    cv_path = "create-compact"
    cv_permission = "add"
    cv_cancel_key = "create"
    cv_formsets = cv_compact_formsets
    cv_action_label_template_code = _("Create compact")
    cv_action_short_label_template_code = _("Create compact")


class QuestionnaireCompactUpdateView(QuestionnaireUpdateView):
    cv_viewset = cv_questionnaire
    cv_key = "compact_update"
    cv_path = "update-compact"
    cv_permission = "change"
    cv_cancel_key = "update"
    cv_formsets = cv_compact_formsets
    cv_action_label_template_code = _("Edit compact")
    cv_action_short_label_template_code = _("Edit compact")


class QuestionnaireDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_questionnaire
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted questionnaire “{{ object }}”")


cv_checklist = ViewSet(model=Checklist, name="checklist", icon_header="fa-solid fa-list-check")


class ChecklistForm(CrispyModelForm):
    class Meta:
        model = Checklist
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]


class ChecklistItemForm(CrispyModelForm):
    class Meta:
        model = ChecklistItem
        fields = ["label", "done"]


ChecklistItemFormSet = inlineformset_factory(
    Checklist,
    ChecklistItem,
    formset=InlineFormSet,
    form=ChecklistItemForm,
    fields=["label", "done"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

cv_checklist_formsets = FormSets(
    formsets=OrderedDict(
        items=FormSet(
            title=_("Items"),
            klass=ChecklistItemFormSet,
            fields=["label", "done"],
            pk_field="id",
            compact_layout=CompactLayout(
                columns=[CompactColumn("label", span=7), CompactColumn("done", span=2)], controls_span=3
            ),
        )
    )
)


class ChecklistTable(Table):
    title = tables.LinkColumn("checklist-update", args=[tables.A("pk")])


class ChecklistListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_checklist
    table_class = ChecklistTable
    cv_context_actions = ["list", "create"]
    cv_list_actions = ["update"]
    cv_paragraph_template_code = _('<a href="{% url "questionnaire-list" %}">Questionnaire examples</a>')


class ChecklistCreateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_checklist
    form_class = ChecklistForm
    cv_formsets = cv_checklist_formsets
    cv_context_actions = ["list", "create"]
    cv_paragraph_template_code = _('<a href="{% url "questionnaire-list" %}">Questionnaire examples</a>')
    cv_message_template_code = _("Created checklist “{{ object }}”")


class ChecklistUpdateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_checklist
    form_class = ChecklistForm
    cv_formsets = cv_checklist_formsets
    cv_context_actions = ["list", "update"]
    cv_paragraph_template_code = _('<a href="{% url "questionnaire-list" %}">Questionnaire examples</a>')
    cv_message_template_code = _("Updated checklist “{{ object }}”")
