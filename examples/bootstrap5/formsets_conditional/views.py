from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.conditional import (
    ConditionalFormSet,
    ConditionalGroup,
    ConditionalGroupModelForm,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.crispy import Column6, Column8, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
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
from formsets_conditional.models import Conference, Session, Speaker

cv_conference = ViewSet(model=Conference, name="conference", icon_header="fa-solid fa-people-group")


class ConferenceForm(ConditionalGroupModelForm):
    # Kind 1: a conditional field-group on the parent form
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_billing"),
            fields=["billing_company", "billing_vat_id"],
            required=["billing_company"],  # the VAT ID stays optional even when on
        ),
    ]

    class Meta:
        model = Conference
        fields = ["name", "with_billing", "billing_company", "billing_vat_id", "with_sessions"]

    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_billing")),
            ToggleGroup(
                "with_billing",
                Row(Column6("billing_company"), Column6("billing_vat_id")),
                legend=_("Billing details"),
            ),
            Row(Column6("with_sessions")),
            Formsets(),
        ]


class SessionForm(CrispyModelForm):
    class Meta:
        model = Session
        fields = ["title"]


class SessionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("title"), self.form_control_col4)]


SessionFormSet = inlineformset_factory(
    Conference,
    Session,
    formset=SessionInlineFormSet,
    form=SessionForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


class SpeakerForm(CrispyModelForm):
    class Meta:
        model = Speaker
        fields = ["name"]


class SpeakerInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("name"), self.form_control_col4)]


SpeakerFormSet = inlineformset_factory(
    Session,
    Speaker,
    formset=SpeakerInlineFormSet,
    form=SpeakerForm,
    fields=["name"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


cv_conference_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        sessions=FormSet(
            title=_("Sessions"),
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Kind 2: only a first-level formset may be conditional. Off => hidden and never
            # validated; purge deletes the existing sessions on save, their speakers cascade.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge"),
            children=OrderedDict(
                # nested under sessions: no conditional here, that would fail crud_views.E310.
                # The speakers follow their session's toggle.
                speakers=FormSet(
                    title=_("Speakers"),
                    klass=SpeakerFormSet,
                    fields=["name"],
                    pk_field="id",
                ),
            ),
        ),
    )
)


class ConferenceTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_billing = tables.Column()
    with_sessions = tables.Column()


class ConferenceListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_conference
    table_class = ConferenceTable


class ConferenceDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_conference
    cv_property_display = [
        {
            "title": _("Conference"),
            "icon": "fas:people-group",
            "properties": [
                "id",
                "name",
                "with_billing",
                "billing_company",
                "billing_vat_id",
                "with_sessions",
                {"path": "session_count", "detail": _("Number of sessions")},
                {"path": "speaker_count", "detail": _("Number of speakers")},
            ],
        },
    ]

    def session_count(self, instance):
        return instance.sessions.count()

    def speaker_count(self, instance):
        return Speaker.objects.filter(session__conference=instance).count()


class ConferenceCreateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_conference
    form_class = ConferenceForm
    cv_formsets: FormSets = cv_conference_formsets
    cv_message_template_code = _("Created conference “{{ object }}”")


class ConferenceUpdateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_conference
    form_class = ConferenceForm
    cv_formsets: FormSets = cv_conference_formsets
    cv_message_template_code = _("Updated conference “{{ object }}”")


class ConferenceDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_conference
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted conference “{{ object }}”")
