from django.utils.translation import gettext_lazy as _
from library.models import Author
from library.views import AuthorForm
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    CardListViewPermissionRequired,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

# A second ViewSet over the same model as Library's cv_author: same data, listed as cards.
cv_author_card = ViewSet(model=Author, name="author_card", icon_header="fa-regular fa-user")


class AuthorCardListView(BreadcrumbMixin, CardListViewPermissionRequired):
    cv_viewset = cv_author_card
    cv_path = ""  # the card list IS the landing page of this ViewSet
    paginate_by = 6  # six cards per page; the seed data gives several pages so pagination is visible
    # signed ordering: the direction is part of each choice, so the toolbar is a single combo
    # (no asc/desc buttons) that submits on change
    cv_order_fields = [
        ("-created_dt", _("Newest first")),
        ("created_dt", _("Oldest first")),
        ("last_name", _("Last name A-Z")),
        ("-last_name", _("Last name Z-A")),
    ]
    cv_order_default = "-created_dt"
    cv_card_actions = [
        CardAction(key="detail", label=_("Details"), variant="primary", flex=True),
        CardAction(key="update", label=_("Edit")),
        CardAction(key="delete", label_mode="icon", variant="tertiary"),
    ]


class AuthorCardDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_author_card
    cv_property_display = [
        {
            "title": _("Author"),
            "icon": "fas:user",
            "properties": ["id", "first_name", "last_name", "pseudonym"],
        },
    ]


class AuthorCardCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_author_card
    form_class = AuthorForm
    cv_message_template_code = _("Created author “{{ object }}”")


class AuthorCardUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author_card
    form_class = AuthorForm
    cv_message_template_code = _("Updated author “{{ object }}”")


class AuthorCardDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_author_card
    form_class = CrispyDeleteForm
    cv_show_related_objects = True
    cv_message_template_code = _("Deleted author “{{ object }}”")
