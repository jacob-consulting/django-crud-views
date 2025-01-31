import django_filters
import django_tables2 as tables

from app.models import Author
from crud_views.lib.table import Table, LinkChildColumn, UUIDLinkDetailColumn
from crud_views.lib.view import cv_property
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    MessageMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired, \
    OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired, DeleteViewPermissionRequired
from crud_views.lib.viewset import ViewSet, path_regs

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=path_regs.UUID
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
    first_name = tables.Column(attrs=Table.col_attr.w20)
    last_name = tables.Column(attrs=Table.col_attr.w30)
    pseudonym = tables.Column(attrs=Table.col_attr.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=Table.col_attr.w10)


class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    model = Author
    filterset_class = AuthorFilter

    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]

    table_class = AuthorTable


class AuthorDetailView(DetailViewPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_properties = ["full_name", "first_name", "last_name", "pseudonym", "books"]

    @cv_property(foo=4711)
    def full_name(self) -> str:
        return f"{self.object.first_name} {self.object.last_name}"

    @cv_property(foo=4711)
    def books(self) -> str:
        return self.object.book_set.count()


class AuthorUpdateView(MessageMixin, UpdateViewPermissionRequired):
    model = Author
    fields = ["first_name", "last_name", "pseudonym"]
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"


class AuthorCreateView(MessageMixin, CreateViewPermissionRequired):
    model = Author
    fields = ["first_name", "last_name", "pseudonym"]
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"


class AuthorDeleteView(MessageMixin, DeleteViewPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"


class AuthorUpView(MessageMixin, OrderedUpViewPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« up"


class AuthorDownView(MessageMixin, OrderedUpDownPermissionRequired):
    model = Author
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« down"

#
# class AuthorManageView(ManageView):
#     model = Author
#     cv = cv_author
