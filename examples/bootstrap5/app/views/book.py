from django.utils.translation import gettext_lazy as _
import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Book
from crud_views.lib.crispy import CrispyModelForm, Column4, Column2, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewTableMixin,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    CreateViewParentMixin,
    MessageMixin,
)
from crud_views.lib.viewset import ViewSet, ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    icon_header="fa-regular fa-address-book",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
)


class BookCreateForm(CrispyModelForm):
    submit_label = _("Create")

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


class BookListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_book
    # cv_list_actions = ["detail", "update", "delete"]

    table_class = BookTable


class BookDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book

    cv_property_display = [
        {
            "title": _("Attributes"),
            "icon": "book-open",
            "description": _("Book details and metadata"),
            "properties": [
                "id",
                "title",
                {"path": "price", "detail": _("Retail price in EUR")},
                "author",
                "created_dt",
                "modified_dt",
            ],
        },
    ]


class BookUpdateView(CrispyModelViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    form_class = BookUpdateForm
    cv_viewset = cv_book


class BookCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book


class BookDeleteView(CrispyModelViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_book
