import django_tables2 as tables
from crispy_forms.layout import Row
from django.views import generic

from crud_views.lib.breadcrumb import BreadcrumbItem
from crud_views.lib.crispy import Column4, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

from breadcrumbs.models import Board, Workspace
from project.views import BreadcrumbMixin


class HostNavBreadcrumbMixin(BreadcrumbMixin):
    """
    Simulates an existing host application injecting its own navigation into the
    crud-views breadcrumb: it keeps the global setting-driven prefix ("Home") and
    appends a fake host-app section in code — per-request logic would go here too.
    """

    def cv_breadcrumb_prefix(self):
        return super().cv_breadcrumb_prefix() + [
            BreadcrumbItem(title="Host application", url_name="breadcrumbs-host"),
        ]


class HostView(generic.TemplateView):
    """The fake host application page the injected prefix item links to."""

    template_name = "breadcrumbs/host.html"


# --------------------------------------------------------------------------- Workspace

cv_workspace = ViewSet(model=Workspace, name="workspace", icon_header="fa-solid fa-diagram-project")


class WorkspaceForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Workspace
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class WorkspaceTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class WorkspaceListView(HostNavBreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_workspace
    table_class = WorkspaceTable


class WorkspaceDetailView(HostNavBreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_workspace
    cv_property_display = [
        {"title": "Workspace", "icon": "diagram-project", "properties": ["id", "name"]},
    ]


class WorkspaceCreateView(HostNavBreadcrumbMixin, CrispyViewMixin, CreateViewPermissionRequired):
    cv_viewset = cv_workspace
    form_class = WorkspaceForm


class WorkspaceUpdateView(HostNavBreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_workspace
    form_class = WorkspaceForm


class WorkspaceDeleteView(HostNavBreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_workspace
    form_class = CrispyDeleteForm


# --------------------------------------------------------------------------- Board (child)

cv_board = ViewSet(model=Board, name="board", parent=ParentViewSet(name="workspace"))


class BoardForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Board
        fields = ["title"]

    def get_layout_fields(self):
        return Row(Column4("title"))


class BoardTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class BoardListView(HostNavBreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_board
    table_class = BoardTable


class BoardDetailView(HostNavBreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_board
    cv_property_display = [
        {"title": "Board", "icon": "chalkboard", "properties": ["id", "title", "workspace"]},
    ]


class BoardCreateView(HostNavBreadcrumbMixin, CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_board
    form_class = BoardForm


class BoardUpdateView(HostNavBreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_board
    form_class = BoardForm


class BoardDeleteView(HostNavBreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_board
    form_class = CrispyDeleteForm
