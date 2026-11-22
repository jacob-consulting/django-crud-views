import django_tables2 as tables
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from bulk_selection.models import Document
from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.crispy import CrispyDeleteForm, CrispyForm, CrispyViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CardListViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
)
from crud_views.lib.viewset import ViewSet

cv_document = ViewSet(model=Document, name="bulk_document", prefix="document", icon_header="fa-regular fa-file")


class DocumentTable(Table):
    title = tables.Column()
    status = tables.Column()
    is_locked = tables.BooleanColumn()
    owner = tables.Column()


class DocumentListView(BreadcrumbMixin, BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_document
    table_class = DocumentTable
    cv_bulk_actions = ("bulk_delete", "archive", "assign_owner")
    cv_list_actions = ["delete"]
    cv_context_actions = ["home", "card"]


class DocumentCardView(BreadcrumbMixin, BulkSelectionMixin, CardListViewPermissionRequired):
    cv_viewset = cv_document
    # Each source lists the actions it offers: Delete is deliberately table-only here.
    cv_bulk_actions = ("archive", "assign_owner")
    paginate_by = 6
    cv_order_fields = ["title", "status"]
    cv_context_actions = ["home", "list"]
    cv_card_actions = []


def document_delete_errors(document):
    return [_("Locked documents cannot be deleted.")] if document.is_locked else []


class DocumentDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm

    def cv_check_delete_protection(self):
        return document_delete_errors(self.object)


class DeleteDocumentsView(BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "bulk_delete"
    cv_path = "bulk-delete"
    cv_permission = "delete"
    cv_icon_action = "delete"
    cv_action_variant = "danger"
    cv_action_label_template_code = _("Delete selected documents")
    cv_action_short_label_template_code = _("Delete")
    cv_success_key = "list"
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} document deleted.{% plural %}{{ count }} documents deleted."
        "{% endblocktranslate %}"
    )

    def cv_bulk_check(self, obj):
        return document_delete_errors(obj)

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.delete(using=self.cv_get_db_alias())


class ArchiveDocumentsView(BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_icon_action = "fas:box-archive"
    cv_action_label_template_code = _("Archive selected documents")
    cv_action_short_label_template_code = _("Archive")
    cv_bulk_confirm = False
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} document archived.{% plural %}{{ count }} documents archived."
        "{% endblocktranslate %}"
    )

    def cv_bulk_check(self, obj):
        if obj.is_locked:
            return [_("Locked documents cannot be archived.")]
        return [] if obj.status == Document.Status.DRAFT else [_("Only drafts can be archived.")]

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.status = Document.Status.ARCHIVED
            document.save(using=self.cv_get_db_alias(), update_fields=["status"])


class AssignOwnerForm(CrispyForm):
    submit_label = _("Assign")
    owner = forms.ModelChoiceField(label=_("Owner"), queryset=get_user_model().objects.none(), required=True)

    def get_layout_fields(self):
        return ["owner"]


class AssignOwnerView(BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "assign_owner"
    cv_path = "assign-owner"
    cv_permission = "change"
    cv_icon_action = "fas:user"
    cv_action_label_template_code = _("Assign owner to selected documents")
    cv_action_short_label_template_code = _("Assign owner")
    form_class = AssignOwnerForm
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "Owner assigned to {{ count }} document.{% plural %}Owner assigned to {{ count }} documents."
        "{% endblocktranslate %}"
    )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Form choices need their own scope, independently of the selected documents.
        form.fields["owner"].queryset = (
            get_user_model().objects.filter(is_active=True, is_superuser=False).order_by("username")
        )
        return form

    def cv_bulk_check(self, obj):
        return [_("Locked documents cannot be reassigned.")] if obj.is_locked else []

    def cv_form_valid(self, context):
        owner = context["form"].cleaned_data["owner"]
        for document in self.cv_bulk_objects:
            document.owner = owner
            document.save(using=self.cv_get_db_alias(), update_fields=["owner"])
