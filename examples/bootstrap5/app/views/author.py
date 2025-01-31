import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from django.utils.translation import gettext as _

from app.models import Author
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, UUIDLinkDetailColumn
from crud_views.lib.table.columns import NaturalTimeColumn, NaturalDayColumn
from crud_views.lib.view import cv_property
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
    DeleteViewPermissionRequired, RedirectChildView
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet, path_regs

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=path_regs.UUID,
    icon_header="fa-regular fa-user"
)


class AuthorCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateForm(AuthorCreateForm):
    """
    Update form has the same fields as the create form
    """
    submit_label = _("Update")


class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(
            Column4("first_name"), Column4("last_name")
        ),
    )


class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Author
        fields = [
            "first_name",
            "last_name",
        ]


class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.col_attr.wID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column(attrs=Table.col_attr.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=Table.col_attr.w10)
    created_dt = NaturalDayColumn()
    modified_dt = NaturalTimeColumn()


class AuthorListView(ListViewTableMixin,
                     ListViewTableFilterMixin,
                     ListViewPermissionRequired):
    model = Author
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper

    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down", "redirect_child"]

    table_class = AuthorTable


class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    model = Author
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"


class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Author
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"


class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Author
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"


class AuthorDetailView(DetailViewPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_properties = [
        "full_name",
        "first_name",
        "last_name",
        "pseudonym",
        "books",
    ]

    @cv_property(foo=4711)
    def full_name(self) -> str:
        return f"{self.object.first_name} {self.object.last_name}"

    @cv_property(foo=4711)
    def books(self) -> str:
        return self.object.book_set.count()


class AuthorUpView(MessageMixin, OrderedUpViewPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« up"


class AuthorDownView(MessageMixin, OrderedUpDownPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« down"


class RedirectBooksView(RedirectChildView):
    cv_action_label = _("Goto Books")
    cv_redirect = "book"
    cv_redirect_key = "list"
    cv_icon_action = "fa-regular fa-address-book"

    cv_viewset = cv_author
