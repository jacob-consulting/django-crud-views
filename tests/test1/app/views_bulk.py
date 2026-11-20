"""Publisher bulk selection fixtures for test_bulk_flow and later bulk scope/lifecycle tests."""

import django_tables2 as tables

from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher

cv_bulk_publisher = ViewSet(model=Publisher, name="bulk_publisher", prefix="bulk-publisher")


class BulkPublisherTable(Table):
    name = tables.Column()


class BulkPublisherListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_bulk_publisher
    table_class = BulkPublisherTable
    cv_bulk_actions = ("archive",)
    cv_list_actions = []
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
