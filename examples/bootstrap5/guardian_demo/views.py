import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkChildColumn, LinkDetailColumn, Table
from crud_views.lib.views import CreateViewParentMixin, ListViewTableMixin, MessageMixin
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import ObjectDetailMixin
from guardian_demo.models import Document, Note

cv_document = GuardianViewSet(
    model=Document,
    name="document",
    icon_header="fa-solid fa-file-lines",
    # equals the GuardianViewSet default, declared so the manage page shows it: as an ancestor of Note requests
    # only an object grant on the Document counts, there is no model permission fallback
    ancestor_policy=AncestorPolicy(provider="guardian", accept_global_perms=False),
)


class DocumentForm(CrispyModelForm):
    class Meta:
        model = Document
        fields = ["title", "body"]

    def get_layout_fields(self):
        return [Row(Column6("title")), Row(Column12("body"))]


class DocumentTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    owner = tables.Column()
    created_dt = tables.DateTimeColumn(verbose_name=_("Created"))
    notes = LinkChildColumn(name="note", verbose_name=_("Notes"), attrs=Table.ca.w10)


class DocumentListView(BreadcrumbMixin, ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_document
    table_class = DocumentTable


class DocumentDetailView(BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_document
    cv_property_display = [
        {"title": _("Document"), "icon": "fas:file-lines", "properties": ["id", "title", "owner", "body"]},
    ]


class DocumentCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_document
    form_class = DocumentForm
    cv_message_template_code = _("Created document “{{ object }}”")

    def cv_form_valid(self, context: dict):
        # the creator owns the document and gets full object-level permissions
        context["form"].instance.owner = self.request.user
        super().cv_form_valid(context)
        for action in ("view", "change", "delete"):
            cv_document.assign_perm(action, self.request.user, self.object)


class DocumentUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    cv_viewset = cv_document
    form_class = DocumentForm
    cv_message_template_code = _("Updated document “{{ object }}”")


class DocumentDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted document “{{ object }}”")


# Notes nest under a document. With the default ancestor policy, requests to notes are authorized against the
# Document object first: Read (list, detail, manage) needs `view` on it, Write (create, update, delete) needs
# `change` on it. The note views then keep their own Note object gates. Nothing is declared here because the
# defaults are the intended policy.
cv_note = GuardianViewSet(
    model=Note,
    name="note",
    parent=ParentViewSet(name="document"),
    icon_header="fa-solid fa-note-sticky",
)


class NoteForm(CrispyModelForm):
    class Meta:
        model = Note
        fields = ["text"]  # author and document are set server-side, never user-supplied

    def get_layout_fields(self):
        return [Row(Column12("text"))]


class NoteTable(Table):
    id = LinkDetailColumn()
    text = tables.Column()
    author = tables.Column()
    created_dt = tables.DateTimeColumn(verbose_name=_("Created"))


class NoteListView(BreadcrumbMixin, ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_note
    table_class = NoteTable


class NoteDetailView(BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_note
    cv_property_display = [
        {"title": _("Note"), "icon": "fas:note-sticky", "properties": ["id", "document", "author", "text"]},
    ]


class NoteCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired
):
    cv_viewset = cv_note
    form_class = NoteForm
    cv_message_template_code = _("Created note “{{ object }}”")

    def cv_form_valid(self, context: dict):
        # CreateViewParentMixin sets the document from the URL; the author is the requesting user
        context["form"].instance.author = self.request.user
        super().cv_form_valid(context)
        # the author and the document owner may read and edit the note; a Document grant never replaces a Note grant
        for user in {self.request.user, self.object.document.owner}:
            for action in ("view", "change", "delete"):
                cv_note.assign_perm(action, user, self.object)


class NoteUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    cv_viewset = cv_note
    form_class = NoteForm
    cv_message_template_code = _("Updated note “{{ object }}”")


class NoteDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    cv_viewset = cv_note
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted note “{{ object }}”")
