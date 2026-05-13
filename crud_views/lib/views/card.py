from django.views import generic

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.view.card import CardAction
from crud_views.lib.settings import crud_views_settings


class CardListView(CrudView, generic.ListView):
    template_name = "crud_views/view_card.html"

    cv_pk: bool = False
    cv_key = "card"
    cv_path = "card"
    cv_object = False
    cv_card_actions: list[CardAction] = []
    cv_card_template: str = "crud_views/tags/card.html"
    cv_context_actions = crud_views_settings.list_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/card.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/card.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/card.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/card.html"
    cv_filter_header_template: str | None = "crud_views/snippets/header/filter.html"
    cv_filter_header_template_code: str | None = None

    # icons
    cv_icon_action = "fa-regular fa-grip"

    @staticmethod
    def cv_get_filter_icon() -> str:
        return crud_views_settings.filter_icon

    @property
    def cv_filter_header(self) -> str:
        return self.render_snippet(
            self.cv_get_meta(),
            self.cv_filter_header_template,
            self.cv_filter_header_template_code,
        )


class CardListViewPermissionRequired(CrudViewPermissionRequiredMixin, CardListView):
    cv_permission = "view"
