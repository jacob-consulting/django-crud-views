import django_filters
import django_tables2 as tables

from app.models import Author
from crud_views.lib.table import Table, LinkChildColumn, UUIDLinkDetailColumn
from crud_views.lib.table.attrs import ColAttr
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
    DeleteViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

cv_author = ViewSet(
    model=Author,
    name="author",
)


class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Author
        fields = [
            "first_name",
            "last_name",
        ]


class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=ColAttr.ID)
    first_name = tables.Column(attrs=ColAttr.w20)
    last_name = tables.Column(attrs=ColAttr.w30)
    pseudonym = tables.Column(attrs=ColAttr.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=ColAttr.w10)


class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    filterset_class = AuthorFilter

    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]

    table_class = AuthorTable


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": [
                "full_name",
                "first_name",
                "last_name",
                "pseudonym",
                "book_count",
            ],
        },
    ]

    # View-Callable Fallback: methods called when the path is not found on the model instance.
    # Signature: (self, instance) -> value

    def full_name(self, instance):
        return f"{instance.first_name} {instance.last_name}"

    def book_count(self, instance):
        return instance.book_set.count()


class AuthorUpdateView(MessageMixin, UpdateViewPermissionRequired):
    fields = ["first_name", "last_name", "pseudonym"]
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"


class AuthorCreateView(MessageMixin, CreateViewPermissionRequired):
    fields = ["first_name", "last_name", "pseudonym"]
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"


class AuthorDeleteView(MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"


class AuthorUpView(MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« up"


class AuthorDownView(MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Successfully moved author »{object}« down"
