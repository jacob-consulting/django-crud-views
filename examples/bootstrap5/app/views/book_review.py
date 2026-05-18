from django.utils.translation import gettext_lazy as _

from app.models import BookReview
from crud_views.lib.crispy import CrispyModelForm, CrispyDeleteForm, CrispyModelViewMixin, Column4, Column6
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    CreateViewParentMixin,
    MessageMixin,
)
from crud_views.lib.viewset import ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)
from crispy_forms.layout import Row

cv_book_review = GuardianViewSet(
    model=BookReview,
    name="book_review",
    parent=ParentViewSet(name="book"),
    icon_header="fa-regular fa-comment",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
)


class BookReviewForm(CrispyModelForm):
    submit_label = _("Save")

    class Meta:
        model = BookReview
        fields = ["reviewer", "text", "rating"]

    def get_layout_fields(self):
        return Row(Column4("reviewer"), Column4("rating"), Column6("text"))


class BookReviewCardListView(GuardianCardListViewPermissionRequired):
    cv_viewset = cv_book_review
    cv_path = ""
    cv_card_container_class = "col-md-12"
    cv_context_actions = ["parent", "card", "filter", "create"]
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]


class BookReviewDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book_review
    cv_context_actions = ["card", "detail", "update", "delete"]
    cv_property_display = [
        {
            "title": _("Review"),
            "icon": "comment",
            "properties": [
                "reviewer",
                "rating",
                "text",
            ],
        },
    ]

class BookReviewCreateView(
    CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired
):
    form_class = BookReviewForm
    cv_viewset = cv_book_review


class BookReviewUpdateView(CrispyModelViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    form_class = BookReviewForm
    cv_viewset = cv_book_review


class BookReviewDeleteView(CrispyModelViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_book_review
