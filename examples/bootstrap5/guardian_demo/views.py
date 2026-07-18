import django_tables2 as tables
from crispy_forms.layout import Row

from crud_views.lib.crispy import Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import ListViewTableMixin, MessageMixin
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import ObjectDetailMixin

from guardian_demo.models import Document

cv_document = GuardianViewSet(model=Document, name="document", icon_header="fa-solid fa-file-lines")


class DocumentForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Document
        fields = ["title", "body"]

    def get_layout_fields(self):
        return [Row(Column6("title")), Row(Column12("body"))]


class DocumentTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    owner = tables.Column()
    created_dt = tables.DateTimeColumn(verbose_name="Created")


class DocumentListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_document
    table_class = DocumentTable


class DocumentDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_document
    cv_property_display = [
        {"title": "Document", "icon": "file-lines", "properties": ["id", "title", "owner", "body"]},
    ]


class DocumentCreateView(CrispyViewMixin, MessageMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_document
    form_class = DocumentForm
    cv_message = "Created document »{object}«"

    def cv_form_valid(self, context: dict):
        # the creator owns the document and gets full object-level permissions
        context["form"].instance.owner = self.request.user
        super().cv_form_valid(context)
        for action in ("view", "change", "delete"):
            cv_document.assign_perm(action, self.request.user, self.object)


class DocumentUpdateView(CrispyViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    cv_viewset = cv_document
    form_class = DocumentForm
    cv_message = "Updated document »{object}«"


class DocumentDeleteView(CrispyViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm
    cv_message = "Deleted document »{object}«"
