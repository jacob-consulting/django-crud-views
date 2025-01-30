import django_tables2 as tables

from tests.test1.app.models import Author
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm, CrispyModelForm
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.view import cv_property
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired, DeleteViewPermissionRequired, ListView, DeleteView, CreateViewPermissionRequired,
    UpdateViewPermissionRequired, DetailViewPermissionRequired
)
from crud_views.lib.viewset import ViewSet, path_regs
from crud_views.lib.crispy import Column4
from crispy_forms.layout import Row

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=path_regs.UUID,
    icon_header="fa-regular fa-user"
)


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()


class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Author
    table_class = AuthorTable

    cv = cv_author
    cv_list_actions = [
        "detail",
        "update", "delete",  # "up", "down", "redirect_child"
    ]


class AuthorDetailView(DetailViewPermissionRequired):
    model = Author
    cv = cv_author
    cv_properties = [
        "full_name",
        "first_name",
        "last_name",
        "pseudonym",
    ]

    @cv_property(foo=4711)
    def full_name(self) -> str:
        return f"{self.object.first_name} {self.object.last_name}"


class AuthorForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Author
    form_class = AuthorForm
    cv = cv_author


class AuthorUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Author
    form_class = AuthorForm
    cv = cv_author


class AuthorDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Author
    form_class = CrispyDeleteForm
    cv = cv_author
