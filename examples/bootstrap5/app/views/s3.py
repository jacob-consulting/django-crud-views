"""
Resource demo: a ViewSet over non-ORM data (a fake in-memory S3 bucket).

Demonstrates: Resource + ResourceViewMixin, md5-hashed pks for path-like
keys, explicit resource_permissions, delete-with-confirm via CustomFormView,
and a form-less ActionView. The bucket resets on server restart.
"""

import hashlib

import django_tables2 as tables

from crud_views.lib.crispy import CrispyViewMixin, CrispyDeleteForm
from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    DetailCustomViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys

FAKE_BUCKET = [
    {"key": "reports/2026/q1.pdf", "size": 431_872},
    {"key": "reports/2026/q2.pdf", "size": 512_004},
    {"key": "images/logo.png", "size": 24_117},
    {"key": "backups/2026-07-01.tar.gz", "size": 10_485_760},
]


class S3File(Resource):
    key: str
    size: int

    class Meta:
        verbose_name = "s3 file"
        verbose_name_plural = "s3 files"
        app_label = "app"
        pk_field = "key_md5"
        pk_type = PrimaryKeys.HEX

    @property
    def key_md5(self) -> str:
        # S3 keys contain "/" — hash them into a URL-safe pk (docs: Resources)
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls.model_validate(row) for row in FAKE_BUCKET]


cv_s3file = ViewSet(
    model=S3File,
    name="s3file",
    icon_header="fa-solid fa-cloud",
    resource_permissions={
        "view": "app.view_s3file",
        "delete": "app.delete_s3file",
    },
)


class S3FileTable(Table):
    key = tables.Column()
    size = tables.Column()


class S3FileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_s3file
    table_class = S3FileTable
    cv_list_actions = ["detail", "delete", "touch"]


class S3FileDetailView(ResourceViewMixin, DetailCustomViewPermissionRequired):
    cv_viewset = cv_s3file
    template_name = "app/s3file_detail.html"


class S3FileDeleteView(ResourceViewMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    cv_key = "delete"
    cv_path = "delete"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    form_class = CrispyDeleteForm
    cv_icon_action = "fa-regular fa-trash-can"
    cv_action_label_template_code = "Delete"
    cv_action_short_label_template_code = "Delete"
    cv_message_template_code = "Deleted »{{ object }}«"
    cv_header_template_code = "Delete S3 file"
    cv_paragraph_template_code = "Confirm deletion of »{{ object }}«"

    def cv_form_valid(self, context):
        # in a real project: boto3 delete_object(Bucket=..., Key=self.object.key)
        FAKE_BUCKET[:] = [row for row in FAKE_BUCKET if row["key"] != self.object.key]


class S3FileTouchView(ResourceViewMixin, ActionViewPermissionRequired):
    cv_key = "touch"
    cv_path = "touch"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    cv_backend_only = True
    cv_icon_action = "fa-regular fa-hand-pointer"
    cv_action_label_template_code = "Touch"
    cv_action_short_label_template_code = "Touch"
    cv_message_template_code = "Touched »{{ object }}«"
    cv_message_template_error_code = "Touch failed for »{{ object }}«"

    def action(self, context) -> bool:
        # in a real project: e.g. copy_object onto itself to refresh metadata
        return True
