import django_tables2 as tables
from crispy_forms.layout import Row, Fieldset
from django.utils.translation import gettext as _

from app.models import Author, Detail
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm, Column8
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    MessageMixin,
    ListViewTableMixin,
    ListViewPermissionRequired,
    DeleteViewPermissionRequired
)
from crud_views.lib.viewset import ViewSet

cv_detail = ViewSet(
    model=Detail,
    name="detail",
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
    cv_context_actions = ListViewPermissionRequired.cv_context_actions
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


class DetailDetailView(DetailViewPermissionRequired):
    model = Detail
    cv_viewset = cv_detail

    property_display = [
        {
            "title": _("Attributes"),
            "icon": "list",
            "description": _("All field types supported by the detail view"),
            "properties": [
                "integer",
                "number",
                {"path": "char", "detail": _("Short text field")},
                {"path": "text", "detail": _("Long text field")},
                "boolean",
                "boolean_two",
                "date",
                "date_time",
            ],
        },
        {
            "title": _("Extra"),
            "icon": "circle-info",
            "description": _("References, timestamps and computed values"),
            "properties": [
                {"path": "id", "detail": _("Unique identifier")},
                "author",
                "foo",
                {"path": "created_dt", "detail": _("When this record was created")},
                {"path": "modified_dt", "detail": _("Last modification timestamp")},
                {"path": "model_prop", "detail": _("Computed from a model property")},
            ],
        },
    ]
