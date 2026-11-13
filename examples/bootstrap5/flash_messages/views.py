from crispy_forms.layout import Row
from django import forms
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column4, Column8, CrispyForm, CrispyViewMixin
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from flash_messages.models import Notice

cv_notice = ViewSet(model=Notice, name="notice", icon_header="fa-regular fa-comment-dots")

#: form value -> django.contrib.messages level
LEVELS = {
    "debug": messages.DEBUG,
    "info": messages.INFO,
    "success": messages.SUCCESS,
    "warning": messages.WARNING,
    "error": messages.ERROR,
}


class MessageForm(CrispyForm):
    submit_label = _("Send message")

    level = forms.ChoiceField(
        label=_("Level"),
        initial="info",
        choices=[
            ("debug", _("Debug")),
            ("info", _("Info")),
            ("success", _("Success")),
            ("warning", _("Warning")),
            ("error", _("Error")),
        ],
    )
    text = forms.CharField(label=_("Text"), max_length=200)

    def get_layout_fields(self):
        return Row(Column4("level"), Column8("text"))


class NoticeComposeView(BreadcrumbMixin, CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    """Queues one flash message at the chosen level, then redirects back here, where {% cv_messages %} shows it."""

    cv_key = "compose"
    cv_permission = "add"
    cv_path = "compose"
    cv_icon_action = "fas:comment-dots"
    cv_viewset = cv_notice
    form_class = MessageForm
    cv_content_template = "flash_messages/compose.html"  # adds one inline {% cv_alert %} above the form
    cv_success_key = "compose"
    cv_cancel_key = "compose"  # the only view: Cancel just clears the form
    cv_context_actions = []  # one page, nothing to link to
    cv_action_label_template_code = _("Compose message")
    cv_action_short_label_template_code = _("Compose")
    cv_header_template_code = _("Flash messages")
    cv_paragraph_template_code = _("Pick a level and a text; the message appears above the page after the redirect")

    def cv_form_valid(self, context):
        data = context["form"].cleaned_data
        messages.add_message(self.request, LEVELS[data["level"]], data["text"])
