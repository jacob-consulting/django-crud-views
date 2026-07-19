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

from conditional.models import Event, Registration, Session

# ---------------- Kind 1: conditional field-group ----------------

cv_registration = ViewSet(model=Registration, name="registration", icon_header="fa-solid fa-user-plus")


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),
            fields=["company_name", "vat_id"],
            required=["company_name"],  # vat_id stays optional even when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend="Company details",
            ),
        ]


class RegistrationTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_company = tables.Column()


class RegistrationListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_registration
    table_class = RegistrationTable


class RegistrationDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_registration
    cv_property_display = [
        {
            "title": "Registration",
            "icon": "user-plus",
            "properties": ["id", "name", "with_company", "company_name", "vat_id"],
        },
    ]


class RegistrationCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message = "Created registration »{object}«"


class RegistrationUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message = "Updated registration »{object}«"


class RegistrationDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = CrispyDeleteForm
    cv_message = "Deleted registration »{object}«"


# ---------------- Kind 2: conditional first-level formset ----------------

cv_event = ViewSet(model=Event, name="event", icon_header="fa-solid fa-calendar")


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["name", "with_sessions"]

    def get_layout_fields(self):
        return [Row(Column6("name")), Row(Column6("with_sessions")), Formsets()]

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

cv_event_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        sessions=FormSet(
            title="Sessions",
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Off => formset hidden & never validated. purge deletes existing rows on save.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge"),
        ),
    )
)


class EventTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_sessions = tables.Column()


class EventListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_event
    table_class = EventTable


class EventDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_event
    cv_property_display = [
        {
            "title": "Event",
            "icon": "calendar",
            "properties": ["id", "name", "with_sessions", {"path": "session_count", "detail": "Number of sessions"}],
        },
    ]

    def session_count(self, instance):
        return instance.sessions.count()


class EventCreateView(CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message = "Created event »{object}«"


class EventUpdateView(CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message = "Updated event »{object}«"


class EventDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_event
    form_class = CrispyDeleteForm
    cv_message = "Deleted event »{object}«"
