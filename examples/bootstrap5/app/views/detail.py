import inspect

import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Fieldset
from django import forms
from django.forms import Form, HiddenInput
from django.forms.widgets import Input, Widget
from django.utils.translation import gettext as _

from app.models import Author, Detail
from crud_views.lib.view import cv_property
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm, Column3, Column8
from crud_views.lib.table import Table, LinkChildColumn, UUIDLinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    MessageMixin,
    ListViewTableMixin,
    ListViewTableFilterMixin,
    ListViewPermissionRequired,
    OrderedUpViewPermissionRequired,
    OrderedUpDownPermissionRequired,
    DeleteViewPermissionRequired, RedirectChildView, DetailLayoutViewPermissionRequired
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet, path_regs

cv_detail = ViewSet(
    model=Detail,
    name="detail",
    pk=path_regs.UUID,
    icon_header="fa-solid fa-circle-info"
)


class DetailForm(CrispyModelForm):
    class Meta:
        model = Detail
        fields = "__all__"

    def get_layout_fields(self):
        return [
            Fieldset("Numbers",
                     Row(
                         Column4("integer"), Column4("number")
                     )),
            Fieldset("Texts",
                     Row(
                         Column4("char"), Column8("text")
                     )),
            Fieldset("Booleans",
                     Row(
                         Column4("boolean"), Column4("boolean_two")
                     )),
            Fieldset("Date an time",
                     Row(
                         Column4("date"), Column4("date_time")
                     )),
            Fieldset("References",
                     Row(
                         Column4("author"), Column4("foo")
                     )),
        ]


class DetailTable(Table):
    id = UUIDLinkDetailColumn()
    integer = tables.Column()
    number = tables.Column()


class DetailListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Detail
    cv_viewset = cv_detail
    table_class = DetailTable


class DetailCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    model = Author
    form_class = DetailForm
    cv_viewset = cv_detail
    cv_message = "Created detail »{object}«"


class DetailUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Detail
    form_class = DetailForm
    cv_viewset = cv_detail
    cv_message = "Updated detail »{object}«"


class DetailDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Detail
    form_class = CrispyDeleteForm
    cv_viewset = cv_detail
    cv_message = "Deleted detail »{object}«"


class DetailDetailView(DetailLayoutViewPermissionRequired):
    model = Detail
    cv_viewset = cv_detail

    @property
    def cv_layout(self) -> Layout:
        return Layout(
            Fieldset("Numbers",
                     Row(
                         Column4("integer"), Column4("number")
                     )),
            Fieldset("Texts",
                     Row(
                         Column4("char"), Column8("text")
                     )),
            Fieldset("Booleans",
                     Row(
                         Column4("boolean"), Column4("boolean_two")
                     )),
            Fieldset("Date an time",
                     Row(
                         Column4("date"), Column4("date_time")
                     )),
            Fieldset("References",
                     Row(
                         Column4("author"), Column4("foo")
                     )),
            Fieldset("Timestamps",
                     Row(
                         Column4("created_dt"), Column4("modified_dt")
                     )),
        )

    @cv_property(foo=4711, label="Ganzer Name")
    def full_name(self) -> str:
        return f"{self.object.first_name} {self.object.last_name}"

    @cv_property("foo", type=bool)
    def bool_true(self) -> bool:
        return True

    @cv_property("foo", type=bool)
    def bool_false(self) -> bool:
        return False

    @cv_property("foo", type=bool)
    def bool_none(self) -> bool:
        return None
