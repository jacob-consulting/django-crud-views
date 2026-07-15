import hashlib

import django_tables2 as tables

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    DetailCustomViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
)
from crud_views.lib.viewset import ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys

# fake in-memory "bucket": tests mutate and reset this module-level list
FAKE_BUCKET = [
    {"key": "reports/2026/q1.pdf", "size": 111},
    {"key": "reports/2026/q2.pdf", "size": 222},
    {"key": "images/logo.png", "size": 333},
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
        # S3 keys contain "/" which no pk regex admits; hash them (spec §9)
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls.model_validate(row) for row in FAKE_BUCKET]


cv_s3file = ViewSet(
    model=S3File,
    name="s3file",
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
    paginate_by = 2  # FAKE_BUCKET has 3 rows -> 2 pages, exercises list pagination
    cv_list_actions = ["detail"]


class S3FileDetailView(ResourceViewMixin, DetailCustomViewPermissionRequired):
    cv_viewset = cv_s3file
    template_name = "app/s3file_detail.html"
