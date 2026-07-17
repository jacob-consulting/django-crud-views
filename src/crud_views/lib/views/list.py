from typing import Iterable

from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.settings import crud_views_settings

# crispy may not be installed
try:
    from crispy_forms.helper import FormHelper
    from crispy_forms import layout
except ImportError:
    FormHelper = object
    layout = None


class ListView(CrudView, generic.ListView):
    template_name = "crud_views/view_list.html"
    cv_content_template = "crud_views/view_list.content.html"

    cv_pk: bool = False  # does not need primary key
    cv_key = "list"
    cv_path = ""
    cv_object = False
    cv_list_actions = crud_views_settings.list_actions
    cv_context_actions = crud_views_settings.list_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/list.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/list.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/list.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/list.html"
    cv_filter_header_template: str | None = "crud_views/snippets/header/filter.html"
    cv_filter_header_template_code: str | None = None

    # icons
    cv_icon_action = "fa-regular fa-rectangle-list"

    @staticmethod
    def cv_get_filter_icon() -> str:
        """
        Currently there is only one global filter icon
        """
        return crud_views_settings.filter_icon

    @property
    def cv_filter_header(self) -> str:
        """
        Get the filter header label
        """
        return self.render_snippet(
            self.cv_get_meta(),
            self.cv_filter_header_template,
            self.cv_filter_header_template_code,
        )

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        yield CheckTemplateOrCode(context=cls, attribute="cv_filter_header_template")


class ListViewPermissionRequired(CrudViewPermissionRequiredMixin, ListView):
    cv_permission = "view"


class ListViewFilterFormHelper(FormHelper):
    """
    Form helper for the filter form
    """

    form_method = "GET"  # filter parameters are always GET
    form_tag = False

    def __init__(self, view, request, form=None):
        super().__init__(form)

        self.view = view
        # add filter control buttons
        self.add_input(
            layout.Submit("submit", _("Apply Filter"), css_id="filter-button"),
        )
        self.add_input(
            layout.Reset(
                "reset",
                _("Reset Filter"),
                css_id="filter-button-reset",
                css_class=crud_views_settings.filter_reset_button_css_class,
            )
        )

        # add hidden fields with control values so a filter submit does not
        # drop the active table sort (ListView) or card order (CardView)
        sort = request.GET.get("sort") or ""
        self.add_input(layout.Hidden("sort", sort))

        order_param = getattr(view, "cv_order_param", "order")
        dir_param = getattr(view, "cv_order_dir_param", "dir")
        order = request.GET.get(order_param) or ""
        direction = request.GET.get(dir_param) or ""
        if order:
            self.add_input(layout.Hidden(order_param, order))
        if direction:
            self.add_input(layout.Hidden(dir_param, direction))
