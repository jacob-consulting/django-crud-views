import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _

from app.models import Qux
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewTableMixin,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    CreateViewParentMixin,
)
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default

cv_qux = ViewSet(
    model=Qux,
    name="qux",
    parent=ParentViewSet(name="foo"),
    icon_header="fa-solid fa-cat",
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="bars", sibling_name="bar", label_template_code="Bars"),
    ],
)


class QuxForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Qux
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class QuxTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class QuxListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Qux
    table_class = QuxTable
    cv_viewset = cv_qux
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["parent", "filter", "create", "bars"]


class QuxDetailView(DetailViewPermissionRequired):
    model = Qux
    cv_viewset = cv_qux
    cv_property_display = [
        {
            "title": _("Properties"),
            "icon": "cat",
            "description": _("Qux attributes"),
            "properties": ["id", "name"],
        },
    ]


class QuxUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Qux
    form_class = QuxForm
    cv_viewset = cv_qux


class QuxCreateView(CrispyModelViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    model = Qux
    form_class = QuxForm
    cv_viewset = cv_qux


class QuxDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Qux
    form_class = CrispyDeleteForm
    cv_viewset = cv_qux
