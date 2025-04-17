from datetime import date

import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext as _

from app.models import Person
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    MessageMixin,
    ListViewTableMixin,
    ListViewPermissionRequired,
    DeleteViewPermissionRequired, CreateViewParentMixin
)
from crud_views.lib.views.detail import PropertyGroup
from crud_views.lib.viewset import ViewSet, ParentViewSet

cv_person = ViewSet(
    model=Person,
    name="members",
    icon_header="fa-regular fa-user",
    parent=ParentViewSet(
        name="group",
        many_to_many_through_attribute="members",
    )
)


class PersonForm(CrispyModelForm):
    class Meta:
        model = Person
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class PersonTable(Table):
    id = LinkDetailColumn(attrs=Table.ca.ID)
    name = tables.Column()
    date_joined = tables.Column(verbose_name=_("Date joined"), empty_values=())

    def render_date_joined(self, value, record):
        return record.membership_set.first().date_joined


class PersonListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Person

    cv_viewset = cv_person
    cv_list_actions = ["detail", "update", "delete",
                       # "redirect_child"
                       ]

    table_class = PersonTable


class PersonCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    model = Person
    form_class = PersonForm
    cv_viewset = cv_person
    cv_message = "Created person »{object}«"

    def cv_parent_many_to_many_through_defaults(self, instance, parent_instance, m2m) -> dict:
        defaults = super().cv_parent_many_to_many_through_defaults(instance, parent_instance, m2m)
        defaults.update({"date_joined": date.today()})
        return defaults


class PersonUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Person
    form_class = PersonForm
    cv_viewset = cv_person
    cv_message = "Updated person »{object}«"


class PersonDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Person
    form_class = CrispyDeleteForm
    cv_viewset = cv_person
    cv_message = "Deleted person »{object}«"


class PersonDetailView(DetailViewPermissionRequired):
    model = Person
    cv_viewset = cv_person
    # cv_context_actions = ["home", "update", "contact", "delete"]

    cv_property_groups = [
        PropertyGroup(
            key="attributes",
            label=_("Attributes"),
            properties=[
                "id",
                "name",
            ]
        ),
    ]
