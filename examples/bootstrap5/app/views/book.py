import django_filters
from crispy_forms.layout import Row, Layout
from django.utils.translation import gettext_lazy as _

from app.models import Book
from crud_views.lib.crispy import CrispyModelForm, Column4, Column2, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    ListViewTableFilterMixin,
    CreateViewParentMixin,
    MessageMixin,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
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


class BookFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(Column4("title")),
    )


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Book
        fields = ["title"]


class BookCardListView(ListViewTableFilterMixin, GuardianCardListViewPermissionRequired):
    cv_viewset = cv_book
    filterset_class = BookFilter
    formhelper_class = BookFilterFormHelper
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]


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
    cv_show_related_objects = True
