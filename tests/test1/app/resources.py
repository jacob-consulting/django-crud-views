import hashlib

import django_tables2 as tables

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
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


TOUCHED: list[str] = []  # side-effect log for the form-less action, reset by tests


class S3FileDeleteConfirmForm(CrispyDeleteForm):
    """Delete form with optional confirmation for easier testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["confirm"].required = False


class S3FileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_s3file
    table_class = S3FileTable
    paginate_by = 2  # FAKE_BUCKET has 3 rows -> 2 pages, exercises list pagination
    cv_list_actions = ["detail", "delete", "touch"]


class S3FileDetailView(ResourceViewMixin, DetailViewPermissionRequired):
    cv_viewset = cv_s3file
    template_name = "app/s3file_detail.html"


class S3FileDeleteView(ResourceViewMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """
    Delete-with-confirm as a custom form view (spec decision 3: no DeleteView
    port — CustomFormView + dev hook IS the delete story for Resources).
    """

    cv_key = "delete"
    cv_path = "delete"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    form_class = S3FileDeleteConfirmForm
    cv_icon_action = "fa-regular fa-trash-can"
    cv_action_label_template_code = "Delete"
    cv_action_short_label_template_code = "Delete"
    cv_message_template_code = "Deleted »{{ object }}«"
    cv_header_template_code = "Delete S3 file"
    cv_paragraph_template_code = "Confirm deletion of »{{ object }}«"

    def cv_form_valid(self, context):
        # the dev hook: this is where delete_object(Bucket=..., Key=obj.key) would go
        FAKE_BUCKET[:] = [row for row in FAKE_BUCKET if row["key"] != self.object.key]


class S3FileTouchView(ResourceViewMixin, ActionViewPermissionRequired):
    """Form-less POST action with a dev hook (spec decision 3).

    Deliberately declares no cv_icon_action: test_list_action_icons pins that
    icon-less actions render without an <i> tag (never class="None").
    """

    cv_key = "touch"
    cv_path = "touch"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    cv_backend_only = True
    cv_action_label_template_code = "Touch"
    cv_action_short_label_template_code = "Touch"
    cv_message_template_code = "Touched »{{ object }}«"
    cv_message_template_error_code = "Touch failed for »{{ object }}«"

    def action(self, context) -> bool:
        # result controllable from the request for testing both branches
        if self.request.GET.get("fail") == "1":
            return False
        TOUCHED.append(self.object.key)
        return True


# nested resource: scoped to a Publisher parent via key prefix "publisher-<pk>/"
NESTED_BUCKET: list[dict] = []


class PublisherFile(Resource):
    key: str
    size: int = 0

    class Meta:
        verbose_name = "publisher file"
        verbose_name_plural = "publisher files"
        app_label = "app"
        pk_field = "key_md5"
        pk_type = PrimaryKeys.HEX

    @property
    def key_md5(self) -> str:
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        # THE nesting contract (spec §8.1): the parent pk arrives as a URL
        # kwarg; scoping the listing is the developer's responsibility.
        prefix = f"publisher-{url_kwargs['publisher_pk']}/"
        return [cls.model_validate(row) for row in NESTED_BUCKET if row["key"].startswith(prefix)]


cv_publisher_file = ViewSet(
    model=PublisherFile,
    name="publisherfile",
    parent=ParentViewSet(name="publisher"),
    resource_permissions={"view": "app.view_s3file"},
)


class PublisherFileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_publisher_file
    table_class = S3FileTable
    cv_list_actions = ["detail"]


class PublisherFileDetailView(ResourceViewMixin, DetailViewPermissionRequired):
    cv_viewset = cv_publisher_file
    template_name = "app/s3file_detail.html"
