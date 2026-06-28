from collections import OrderedDict
from typing import List

import django_tables2 as tables
from crispy_forms.layout import Row, LayoutObject
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext, gettext_lazy as _

from app.models.conditional import Registration, Event, Session
from crud_views.lib.conditional import (
    ConditionalGroup,
    ConditionalGroupModelForm,
    ConditionalFormSet,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.crispy import Column6, Column8, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.formsets import FormSets, FormSet, FormSetMixin, InlineFormSet
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

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
                legend=_("Company details"),
            ),
        ]


class RegistrationTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_company = tables.Column()


class RegistrationListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Registration
    table_class = RegistrationTable
    cv_viewset = cv_registration


class RegistrationDetailView(DetailViewPermissionRequired):
    model = Registration
    cv_viewset = cv_registration
    cv_property_display = [
        {
            "title": _("Registration"),
            "icon": "user-plus",
            "description": _("Registration details"),
            "properties": ["id", "name", "with_company", "company_name", "vat_id"],
        },
    ]


class RegistrationCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Registration
    form_class = RegistrationForm
    cv_viewset = cv_registration


class RegistrationUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Registration
    form_class = RegistrationForm
    cv_viewset = cv_registration


class RegistrationDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Registration
    form_class = CrispyDeleteForm
    cv_viewset = cv_registration


# ---------------- Kind 2: conditional first-level formset ----------------

cv_event = ViewSet(model=Event, name="event", icon_header="fa-solid fa-calendar")


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["name", "with_sessions"]

    def get_layout_fields(self):
        from crud_views.lib.formsets import Formsets

        return [
            Row(Column6("name")),
            Row(Column6("with_sessions")),
            Formsets(),
        ]

    @property
    def helper(self):
        # A form rendering Formsets() must not emit its own <form> tag: the CRUD
        # create/update template already wraps the fields in <form class="cv-form">.
        # Without this, crispy nests a second <form>, the browser closes cv-form
        # early, and formset.js cannot bind the add/reorder controls.
        h = super().helper
        h.form_tag = False
        return h


class SessionForm(CrispyModelForm):
    class Meta:
        model = Session
        fields = ["title"]


class SessionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self) -> List[LayoutObject]:
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
            title=gettext("Sessions"),
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Off => formset hidden & never validated. "skip" keeps existing rows;
            # switch to on_off="purge" to delete them on save when toggled off.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge"),
        ),
    )
)


class EventTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_sessions = tables.Column()


class EventListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Event
    table_class = EventTable
    cv_viewset = cv_event


class EventDetailView(DetailViewPermissionRequired):
    model = Event
    cv_viewset = cv_event
    cv_property_display = [
        {
            "title": _("Event"),
            "icon": "calendar",
            "description": _("Event details"),
            "properties": ["id", "name", "with_sessions"],
        },
    ]


class EventCreateView(CrispyModelViewMixin, FormSetMixin, CreateViewPermissionRequired):
    model = Event
    form_class = EventForm
    cv_viewset = cv_event
    cv_formsets: FormSets = cv_event_formsets


class EventUpdateView(CrispyModelViewMixin, FormSetMixin, UpdateViewPermissionRequired):
    model = Event
    form_class = EventForm
    cv_viewset = cv_event
    cv_formsets: FormSets = cv_event_formsets


class EventDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Event
    form_class = CrispyDeleteForm
    cv_viewset = cv_event
