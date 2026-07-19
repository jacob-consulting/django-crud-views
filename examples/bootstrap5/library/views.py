import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row

from crud_views.lib.crispy import Column2, Column4, Column6, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table, UUIDLinkDetailColumn
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    OrderedUpDownPermissionRequired,
    OrderedUpViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

from library.models import Author, Book
from project.views import BreadcrumbMixin

# --------------------------------------------------------------------------- Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")


class AuthorForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Author
        fields = ["first_name", "last_name"]


class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("first_name"), Column4("last_name")))


class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()


class AuthorListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper


class AuthorDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_property_display = [
        {
            "title": "Author",
            "icon": "user",
            "properties": [
                "id",
                "first_name",
                "last_name",
                "pseudonym",
                {"path": "book_count", "detail": "Number of books (computed on the view)"},
            ],
        },
    ]

    def book_count(self, instance):
        # view-callable fallback: called when the path is not found on the model
        return instance.book_set.count()


class AuthorCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message = "Created author »{object}«"


class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message = "Updated author »{object}«"


class AuthorDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_author
    form_class = CrispyDeleteForm
    cv_message = "Deleted author »{object}«"
    cv_show_related_objects = True


# --------------------------------------------------------------------------- Book

cv_book = ViewSet(model=Book, name="book", icon_header="fa-solid fa-book")


class BookForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Book
        fields = ["title", "author", "price"]

    def get_layout_fields(self):
        return Row(Column6("title"), Column4("author"), Column2("price"))


class BookTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    author = tables.Column()
    price = tables.Column()


class BookListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_book
    table_class = BookTable
    cv_list_actions = ["detail", "update", "delete", "up", "down"]


class BookDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {"title": "Book", "icon": "book", "properties": ["id", "title", "author", "price"]},
    ]


class BookCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookForm
    cv_message = "Created book »{object}«"


class BookUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookForm
    cv_message = "Updated book »{object}«"


class BookDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_book
    form_class = CrispyDeleteForm
    cv_message = "Deleted book »{object}«"


class BookUpView(BreadcrumbMixin, MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_book
    cv_message = "Moved book »{object}« up"


class BookDownView(BreadcrumbMixin, MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_book
    cv_message = "Moved book »{object}« down"
