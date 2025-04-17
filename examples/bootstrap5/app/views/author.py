import django_filters
import django_tables2 as tables
from crispy_forms.layout import Layout, Row
from django.forms.fields import CharField
from django.utils.translation import gettext as _

from app.models import Author
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm, Column12
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
from crud_views.lib.views.detail import PropertyGroup, Property
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.views.properties import r
from crud_views.lib.viewset import ViewSet

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=ViewSet.PK.UUID,
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
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column(attrs=Table.ca.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=Table.ca.w10)
    created_dt = NaturalDayColumn()
    modified_dt = NaturalTimeColumn()


class AuthorListView(ListViewTableMixin,
                     ListViewTableFilterMixin,
                     ListViewPermissionRequired):
    # generic view config
    model = Author

    # table config
    table_class = AuthorTable

    # filter config
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper

    # viewset config
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down", "redirect_child", "contact"]


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
    # cv_context_actions = ["home", "update", "contact", "delete"]

    cv_property_groups = [
        PropertyGroup(
            key="attributes",
            label=_("Attributes"),
            properties=[
                "xyz",
                "a_boolean",
                "b_boolean",
                "full_name",
                "first_name",
                "last_name",
            ]
        ),
        PropertyGroup(
            key="extra",
            label=_("Extra"),
            properties=[
                Property(name="id", label="UUID"),
                "pseudonym",
                "books",
                "abc",
            ]
        ),
    ]

    @cv_property(label="Full Name")
    def full_name(self) -> str:
        return f"{self.object.first_name} {self.object.last_name}"

    @cv_property(label=_("Number of books"))
    def books(self) -> str:
        return self.object.book_set.count()

    @cv_property(label=_("A boolean 1"), renderer=r.boolean)
    def a_boolean(self) -> bool:
        return True

    @cv_property(label=_("A boolean 2"), renderer=r.boolean)
    def b_boolean(self) -> bool:
        return False


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


class AuthorContactForm(CrispyModelForm):
    submit_label = _("Send")

    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        return Column12("subject"), Column12("body")


class AuthorContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    model = Author
    cv_key = "contact"
    cv_path = "contact"
    cv_icon_action = "fa-solid fa-envelope"
    cv_viewset = cv_author
    form_class = AuthorContactForm

    cv_message_template_code = "Successfully contacted author »{object}«"

    cv_context_actions = ["parent", "detail", "update", "delete", "contact"]
    cv_header_template_code = _("Contact Author")
    cv_paragraph_template_code = _("Send a message to the Author")
    cv_action_label_template_code = _("Contact Author")
    cv_action_short_label_template_code = _("Contact Author Short")

    def form_valid(self, form):
        return super().form_valid(form)
