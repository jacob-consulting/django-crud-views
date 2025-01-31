import django_tables2 as tables

from app.models import Book
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet, path_regs

cv_book = ViewSet(
    model=Book,
    name="book",
    pk=path_regs.UUID,
    parent=ParentViewSet(name="author"),
)


class BookTable(Table):
    id = UUIDLinkDetailColumn()
    title = tables.Column()
    price = tables.Column()
    author = tables.Column()


class BookListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Book
    cv_viewset = cv_book
    # cv_list_actions = ["detail", "update", "delete"]

    table_class = BookTable


class BookDetailView(DetailViewPermissionRequired):
    model = Book
    cv_viewset = cv_book


class BookUpdateView(UpdateViewPermissionRequired):
    model = Book
    fields = ["title", "price"]
    cv_viewset = cv_book


class BookCreateView(CreateViewPermissionRequired):
    model = Book
    fields = ["title", "price"]
    cv_viewset = cv_book


class BookDeleteView(DeleteViewPermissionRequired):
    model = Book
    cv_viewset = cv_book
