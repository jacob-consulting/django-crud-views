import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Book
from crud_views.lib.crispy import CrispyModelForm, Column4, Column2, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, \
    CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired, CreateViewParentMixin, MessageMixin
from crud_views.lib.viewset import ViewSet, ParentViewSet

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    icon_header="fa-regular fa-address-book"  # <i class="fa-regular fa-address-book"></i>
)


class BookCreateForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Book
        fields = ["title", "price"]

    def get_layout_fields(self):
        return Row(Column4("title"), Column2("price"))


class BookUpdateForm(BookCreateForm):
    """
    Update form has the same fields as the create form
    """


class BookTable(Table):
    id = UUIDLinkDetailColumn()
    title = tables.Column()
    price = tables.Column()
    author = tables.Column()


class BookListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_book
    # cv_list_actions = ["detail", "update", "delete"]

    table_class = BookTable


class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book

    property_display = [
        {
            "title": "Attributes",
            "icon": "book-open",
            "description": "Book details and metadata",
            "properties": [
                "id",
                "title",
                {"path": "price", "detail": "Retail price in EUR"},
                "author",
                "created_dt",
                "modified_dt",
            ],
        },
    ]


class BookUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = BookUpdateForm
    cv_viewset = cv_book


class BookCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book


class BookDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_book
