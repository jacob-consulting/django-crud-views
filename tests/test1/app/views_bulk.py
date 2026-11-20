"""Publisher bulk selection fixtures for test_bulk_flow and later bulk scope/lifecycle tests."""

import django_tables2 as tables
from django import forms

from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.crispy import CrispyForm
from crud_views.lib.deletion import inspect_deletion
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CardListViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet
from tests.test1.app.models import Author, Book, BulkCode, Publisher
from tests.test1.app.views import PublisherFilterFormHelper, PublisherOrderFilter

cv_bulk_publisher = ViewSet(model=Publisher, name="bulk_publisher", prefix="bulk-publisher")
cv_bulk_author = ViewSet(model=Author, name="bulk_author", prefix="bulk-author")
cv_bulk_code = ViewSet(model=BulkCode, name="bulk_code", prefix="bulk-code")


class BulkAuthorTable(Table):
    first_name = tables.Column()


class BulkAuthorListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_author
    table_class = BulkAuthorTable
    cv_bulk_actions = ("mark",)
    cv_list_actions = []
    cv_context_actions = ["home"]


class BulkAuthorMarkView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_author
    cv_key = "mark"
    cv_path = "mark"
    cv_permission = "change"
    cv_action_label_template_code = "Mark selected"
    cv_action_short_label_template_code = "Mark"
    cv_success_key = "list"

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.pseudonym = "marked"
            obj.save(using=self.cv_get_db_alias())


class BulkCodeTable(Table):
    code = tables.Column()


class BulkCodeListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_code
    table_class = BulkCodeTable
    cv_bulk_actions = ("mark",)
    cv_list_actions = []
    cv_context_actions = ["home"]


class BulkCodeMarkView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_code
    cv_key = "mark"
    cv_path = "mark"
    cv_permission = "change"
    cv_action_label_template_code = "Mark selected"
    cv_action_short_label_template_code = "Mark"
    cv_success_key = "list"

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.label = "marked"
            obj.save(using=self.cv_get_db_alias())


class BulkPublisherTable(Table):
    name = tables.Column()


cv_bulk_filter = ViewSet(model=Publisher, name="bulk_filter", prefix="bulk-filter")


class BulkFilterListView(BulkSelectionMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_filter
    table_class = BulkPublisherTable
    filterset_class = PublisherOrderFilter
    formhelper_class = PublisherFilterFormHelper
    paginate_by = 2
    cv_bulk_actions = ("mark",)
    cv_list_actions = []
    cv_context_actions = ["home"]


class BulkFilterCardView(BulkSelectionMixin, ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_bulk_filter
    filterset_class = PublisherOrderFilter
    formhelper_class = PublisherFilterFormHelper
    paginate_by = 2
    cv_order_fields = ["name"]
    cv_bulk_actions = ("mark",)
    cv_context_actions = ["home"]


class BulkFilterMarkView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_filter
    cv_key = "mark"
    cv_path = "mark"
    cv_permission = "change"
    cv_action_label_template_code = "Mark selected"
    cv_action_short_label_template_code = "Mark"
    cv_success_key = "list"

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.name += " (marked)"
            obj.save(using=self.cv_get_db_alias())


cv_bulk_book = ViewSet(
    model=Book, name="bulk_book", prefix="bulk-book", parent=ParentViewSet(name="bulk_publisher", attribute="publisher")
)


class BulkBookTable(Table):
    title = tables.Column()


class BulkBookListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_book
    table_class = BulkBookTable
    cv_bulk_actions = ("mark",)
    cv_list_actions = []
    cv_context_actions = ["home"]


class BulkBookMarkView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_book
    cv_key = "mark"
    cv_path = "mark"
    cv_permission = "change"
    cv_action_label_template_code = "Mark selected"
    cv_action_short_label_template_code = "Mark"
    cv_success_key = "list"

    def get_queryset(self):
        return Book.objects.all()

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.title += " (marked)"
            obj.save(using=self.cv_get_db_alias())


class BulkTenantViewSet(ViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).exclude(name__startswith="Foreign")


cv_bulk_tenant = BulkTenantViewSet(model=Publisher, name="bulk_tenant", prefix="bulk-tenant")


class BulkTenantListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_tenant
    table_class = BulkPublisherTable
    cv_bulk_actions = ("mark",)
    cv_list_actions = []
    cv_context_actions = ["home"]

    def get_queryset(self):
        return super().get_queryset().exclude(name__startswith="Unlisted")


class BulkTenantMarkView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_tenant
    cv_key = "mark"
    cv_path = "mark"
    cv_permission = "change"
    cv_action_label_template_code = "Mark selected"
    cv_action_short_label_template_code = "Mark"
    cv_success_key = "list"

    def get_queryset(self):
        return Publisher.objects.all()

    def cv_bulk_has_permission(self, obj):
        return not obj.name.startswith("Private")

    def cv_bulk_check(self, obj):
        return ["Locked publishers cannot be marked."] if obj.name.startswith("Locked") else []

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.name += " (marked)"
            obj.save(using=self.cv_get_db_alias())


class BulkTenantNarrowView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_tenant
    cv_key = "narrow"
    cv_path = "narrow"
    cv_permission = "change"
    cv_action_label_template_code = "Mark visible"
    cv_action_short_label_template_code = "Mark visible"
    cv_success_key = "list"
    cv_bulk_confirm = False

    def get_queryset(self):
        return super().get_queryset().exclude(name__startswith="Hidden")

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.name += " (marked)"
            obj.save(using=self.cv_get_db_alias())


class BulkPublisherListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_publisher
    table_class = BulkPublisherTable
    cv_bulk_actions = ("archive", "archive_now", "rename", "bulk_delete")
    cv_list_actions = []
    cv_context_actions = ["home"]


class BulkPublisherCardView(BulkSelectionMixin, CardListViewPermissionRequired):
    cv_viewset = cv_bulk_publisher
    cv_bulk_actions = ("archive", "archive_now")
    paginate_by = 2
    cv_order_fields = ["name"]
    cv_context_actions = ["home"]


class BulkPublisherArchiveView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_publisher
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_action_label_template_code = "Archive selected publishers"
    cv_action_short_label_template_code = "Archive"
    cv_success_key = "list"

    def cv_bulk_check(self, obj):
        return ["Locked publishers cannot be archived."] if obj.name.startswith("Locked") else []

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.name += " (archived)"
            obj.save(using=self.cv_get_db_alias())


class BulkPublisherArchiveNowView(BulkPublisherArchiveView):
    cv_viewset = cv_bulk_publisher
    cv_key = "archive_now"
    cv_path = "archive-now"
    cv_bulk_confirm = False
    cv_action_short_label_template_code = "Archive now"


class BulkRenameForm(CrispyForm):
    suffix = forms.CharField()
    submit_label = "Rename"

    def get_layout_fields(self):
        return ["suffix"]


class BulkPublisherRenameView(BulkPublisherArchiveView):
    cv_viewset = cv_bulk_publisher
    cv_key = "rename"
    cv_path = "rename"
    cv_bulk_confirm = False
    form_class = BulkRenameForm
    cv_message_template_code = "{{ view.cv_bulk_objects|length }} publishers renamed."

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.name += context["form"].cleaned_data["suffix"]
            obj.save(using=self.cv_get_db_alias())


def publisher_delete_errors(publisher):
    return ["Locked publishers cannot be deleted."] if publisher.name.startswith("Locked") else []


class BulkPublisherDeleteView(BulkFormViewPermissionRequired):
    cv_viewset = cv_bulk_publisher
    cv_key = "bulk_delete"
    cv_path = "bulk-delete"
    cv_permission = "delete"
    cv_action_label_template_code = "Delete selected publishers"
    cv_action_short_label_template_code = "Delete"
    cv_icon_action = "delete"
    cv_success_key = "list"

    def cv_bulk_check(self, obj):
        errors = publisher_delete_errors(obj)
        inspection = inspect_deletion(obj, using=self.cv_get_db_alias())
        if inspection.related.protected:
            errors.append("Deletion is blocked by related records.")
        if not inspection.complete:
            errors.append("This object's deletion needs a dedicated application action.")
        return errors

    def cv_form_valid(self, context):
        for obj in self.cv_bulk_objects:
            obj.delete(using=self.cv_get_db_alias())


class PublisherChanged(Exception):
    """A selected publisher disappeared or became blocked before the locked read."""


class BulkPublisherLockedArchiveView(BulkPublisherArchiveView):
    cv_viewset = cv_bulk_publisher
    cv_key = "archive_locked"
    cv_path = "archive-locked"
    cv_action_short_label_template_code = "Archive with lock"
    cv_atomic = True  # select_for_update needs the transaction.

    def cv_form_valid(self, context):
        keys = [obj.pk for obj in self.cv_bulk_objects]
        rows = list(
            self.cv_viewset.model._default_manager.using(self.cv_get_db_alias()).select_for_update().filter(pk__in=keys)
        )
        if len(rows) != len(keys):
            raise PublisherChanged("A selected publisher was deleted.")
        if any(self.cv_bulk_check(obj) for obj in rows):
            raise PublisherChanged("A selected publisher became blocked.")
        for obj in rows:
            obj.name += " (archived)"
            obj.save(using=self.cv_get_db_alias())
