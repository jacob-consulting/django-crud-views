import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _

from app.models import Bar
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewTableMixin,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    CreateViewParentMixin,
)
from crud_views.lib.view import SiblingContextButton, ChildContextButton
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default

cv_bar = ViewSet(
    model=Bar,
    name="bar",
    parent=ParentViewSet(name="foo"),
    icon_header="fa-solid fa-bone",
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="quxes", sibling_name="qux", label_template_code="Quxes"),
    ],
)


class BarForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Bar
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class BarTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    baz = LinkChildColumn(name="baz", verbose_name=_("Baz"), empty_values=())


class BarListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Bar
    table_class = BarTable
    cv_viewset = cv_bar
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["parent", "filter", "create", "quxes"]


class BarDetailView(DetailViewPermissionRequired):
    model = Bar
    cv_viewset = cv_bar
    # View-level button: declared on this view only, so it renders on the Bar
    # detail page but not on bar's list/update/etc. Contrast with the ViewSet-level
    # "Quxes" sibling button (cv_bar.context_buttons), which the list view shows.
    cv_context_buttons = [
        ChildContextButton(key="bazzes", child_name="baz", label_template_code="Bazzes"),
    ]
    cv_context_actions = ["home", "detail", "update", "delete", "bazzes"]
    cv_property_display = [
        {
            "title": _("Properties"),
            "icon": "bone",
            "description": _("Bar attributes"),
            "properties": [
                "id",
                "name",
            ],
        },
    ]


class BarUpdateView(CrispyViewMixin, UpdateViewPermissionRequired):
    model = Bar
    form_class = BarForm

    cv_viewset = cv_bar


class BarCreateView(CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    model = Bar
    form_class = BarForm
    cv_viewset = cv_bar


class BarDeleteView(CrispyViewMixin, DeleteViewPermissionRequired):
    model = Bar
    form_class = CrispyDeleteForm
    cv_viewset = cv_bar
    cv_show_related_objects = True
    cv_link_related_objects = True
