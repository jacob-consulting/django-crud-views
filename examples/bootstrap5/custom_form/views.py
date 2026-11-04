import django_tables2 as tables
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column6, Column12, CrispyForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin, MessageMixin
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired, CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from custom_form.models import Contact

cv_contact = ViewSet(model=Contact, name="contact", icon_header="fa-regular fa-address-book")


class ContactTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    email = tables.Column()
    last_reminded_dt = tables.DateTimeColumn()


class ContactListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_contact
    table_class = ContactTable
    # "remind" is an object view, so it is a row action; "invite" needs no object, so it is a context action
    cv_list_actions = ["detail", "remind"]
    cv_context_actions = ["home", "invite"]


class ContactDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_contact
    cv_context_actions = ["home", "remind"]
    cv_property_display = [
        {
            "title": _("Contact"),
            "icon": "fas:address-book",
            "properties": ["id", "name", "email", "last_reminded_dt"],
        },
    ]


class RemindForm(CrispyForm):
    submit_label = _("Send reminder")

    note = forms.CharField(label=_("Note"), required=True)

    def get_layout_fields(self):
        return Column12("note")


class ContactRemindView(BreadcrumbMixin, MessageMixin, CrispyViewMixin, CustomFormViewPermissionRequired):
    """An object-based custom form: loads the contact from the URL, then acts on it."""

    cv_key = "remind"
    cv_path = "remind"
    cv_icon_action = "fas:bell"
    cv_viewset = cv_contact
    form_class = RemindForm
    cv_action_label_template_code = _("Remind")
    cv_action_short_label_template_code = _("Remind")

    cv_message_template_code = _("Reminded contact “{{ object }}”")
    cv_context_actions = ["home", "detail", "remind"]
    cv_header_template_code = _("Remind contact")
    cv_paragraph_template_code = _("Send a reminder note to this contact")

    def cv_form_valid(self, context):
        contact = context["object"]
        # context["form"].cleaned_data["note"] would go into the mail or task you send here
        contact.last_reminded_dt = timezone.now()
        contact.save(update_fields=["last_reminded_dt"])


class InviteForm(CrispyForm):
    submit_label = _("Invite")

    email = forms.EmailField(label=_("Email"), required=True)

    def get_layout_fields(self):
        return Column6("email")


class ContactInviteView(BreadcrumbMixin, MessageMixin, CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    """A non-object custom form: no pk in the URL, it creates a new contact."""

    cv_key = "invite"
    cv_path = "invite"
    cv_icon_action = "fas:envelope"
    cv_viewset = cv_contact
    form_class = InviteForm
    cv_action_label_template_code = _("Invite")
    cv_action_short_label_template_code = _("Invite")

    cv_message_template_code = _("Invited “{{ form.cleaned_data.email }}”")
    cv_context_actions = ["home", "invite"]
    cv_header_template_code = _("Invite contact")
    cv_paragraph_template_code = _("Add a new contact by email address")

    def cv_form_valid(self, context):
        Contact.objects.create(email=context["form"].cleaned_data["email"])
