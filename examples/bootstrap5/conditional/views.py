from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory

from crud_views.lib.conditional import (
    ConditionalFormSet,
    ConditionalGroup,
    ConditionalGroupModelForm,
    ModelFieldToggle,
    ToggleGroup,
    UIFieldToggle,
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

from conditional.models import Event, Registration, Session, Speaker
from project.views import BreadcrumbMixin

# ---------------- Kind 1: conditional field-group ----------------

cv_registration = ViewSet(model=Registration, name="registration", icon_header="fa-solid fa-user-plus")


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),
            fields=["company_name", "vat_id"],
            required=["company_name"],  # vat_id stays optional even when on
        ),
        # UIFieldToggle: a transient checkbox the mixin injects — it is not a model
        # field, only "note" is stored.
        ConditionalGroup(
            toggle=UIFieldToggle("add_note"),
            fields=["note"],
            required=[],  # note stays optional even when the toggle is on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id", "note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A UIFieldToggle is not persisted, so derive its initial state from the
        # instance — otherwise updating a registration with a note would render
        # the toggle off and clear the note on the next save.
        self.fields["add_note"].label = "Add a note"
        self.fields["add_note"].initial = bool(self.instance.pk and self.instance.note)

    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend="Company details",
            ),
            Row(Column6("add_note")),
            ToggleGroup("add_note", Row(Column8("note"))),
        ]


class RegistrationTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_company = tables.Column()


class RegistrationListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_registration
    table_class = RegistrationTable


class RegistrationDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_registration
    cv_property_display = [
        {
            "title": "Registration",
            "icon": "user-plus",
            "properties": ["id", "name", "with_company", "company_name", "vat_id", "note"],
        },
    ]


class RegistrationCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message_template_code = "Created registration »{{ object }}«"


class RegistrationUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message_template_code = "Updated registration »{{ object }}«"


class RegistrationDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = CrispyDeleteForm
    cv_message_template_code = "Deleted registration »{{ object }}«"


# ---------------- Kind 2: conditional first-level formset ----------------

cv_event = ViewSet(model=Event, name="event", icon_header="fa-solid fa-calendar")


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["name", "with_sessions", "with_speakers"]

    def get_layout_fields(self):
        return [Row(Column6("name")), Row(Column6("with_sessions"), Column6("with_speakers")), Formsets()]

    @property
    def helper(self):
        # the formsets render their own form tags
        h = super().helper
        h.form_tag = False
        return h


class SessionForm(CrispyModelForm):
    class Meta:
        model = Session
        fields = ["title"]


class SessionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("title"), self.form_control_col4)]


SessionFormSet = inlineformset_factory(
    Event,
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
    Event,
    Speaker,
    formset=SpeakerInlineFormSet,
    form=SpeakerForm,
    fields=["name"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

cv_event_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        sessions=FormSet(
            title="Sessions",
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Off => formset hidden & never validated. purge DELETES existing rows
            # on save — prefer skip (below) unless deletion is intended.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge"),
        ),
        speakers=FormSet(
            title="Speakers",
            klass=SpeakerFormSet,
            fields=["name"],
            pk_field="id",
            # skip is the safe default: untoggling hides the formset but existing
            # rows survive the save.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_speakers"), on_off="skip"),
        ),
    )
)


class EventTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_sessions = tables.Column()


class EventListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_event
    table_class = EventTable


class EventDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_event
    cv_property_display = [
        {
            "title": "Event",
            "icon": "calendar",
            "properties": [
                "id",
                "name",
                "with_sessions",
                {"path": "session_count", "detail": "Number of sessions"},
                "with_speakers",
                {"path": "speaker_count", "detail": "Number of speakers"},
            ],
        },
    ]

    def session_count(self, instance):
        return instance.sessions.count()

    def speaker_count(self, instance):
        return instance.speakers.count()


class EventCreateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message_template_code = "Created event »{{ object }}«"


class EventUpdateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message_template_code = "Updated event »{{ object }}«"


class EventDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_event
    form_class = CrispyDeleteForm
    cv_message_template_code = "Deleted event »{{ object }}«"
