from typing import Iterable

from django.views import generic
from django_object_detail.views import ObjectDetailMixin

from crud_views.lib.check import Check
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DetailView(ObjectDetailMixin, CrudView, generic.DetailView):
    template_name = "crud_views/view_detail.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    # icons
    cv_icon_action = "fa-regular fa-eye"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()


class DetailViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailView):  # this file
    cv_permission = "view"
