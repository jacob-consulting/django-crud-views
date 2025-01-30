from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin, ViewContext
from crud_views.lib.settings import crud_views_settings

# crispy may not be installed
try:
    from crispy_forms.helper import FormHelper
    from crispy_forms import layout
except ImportError:
    FormHelper = object
    layout = None


class ListView(ViewSetView, generic.ListView):
    template_name = "crud_views/view_list.html"

    cv_pk: bool = False  # does not need primary key
    cv_key = "list"
    cv_path = ""
    cv_object = False
    cv_list_actions = crud_views_settings.list_actions
    cv_context_actions = crud_views_settings.list_context_actions

    # texts and labels
    cv_header_template: str = crud_views_settings.list_header_template
    cv_header_template_code: str = crud_views_settings.list_header_template_code
    cv_paragraph_template: str = crud_views_settings.list_paragraph_template
    cv_paragraph_template_code: str = crud_views_settings.list_paragraph_template_code
    cv_action_label_template: str = crud_views_settings.list_action_label_template
    cv_action_label_template_code: str = crud_views_settings.list_action_label_template_code
    cv_action_short_label_template: str = crud_views_settings.list_action_short_label_template
    cv_action_short_label_template_code: str = crud_views_settings.list_action_short_label_template_code

    cv_filter_header_template: str | None = crud_views_settings.filter_header_template
    cv_filter_header_template_code: str | None = crud_views_settings.filter_header_template_code

    cv_icon_action = "fa-regular fa-rectangle-list"

    # todo: add check for cv_filter_header_template/cv_filter_header_template_code

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
        return self.render_snippet(self.cv_get_meta(),
                                   self.cv_filter_header_template,
                                   self.cv_filter_header_template_code, )


class ListViewPermissionRequired(ViewSetViewPermissionRequiredMixin, ListView):
    cv_permission = "view"


class ListViewFilterFormHelper(FormHelper):
    """
    Form helper for the filter form
    """
    form_method = 'GET'  # filter parameters are always GET
    form_tag = False  # todo really?, just add hidden stuff

    def __init__(self, request, form=None):
        super().__init__(form)

        # add filter control buttons
        self.add_input(layout.Submit('submit', 'Apply Filter', css_id="filter-button"), )
        self.add_input(layout.Reset(
            'reset',
            _('Reset Filter'),
            css_id="filter-button-reset",
            css_class=crud_views_settings.filter_reset_button_css_class
        ))

        # add hidden fields with control values
        sort = request.GET.get("sort") or ""
        self.add_input(layout.Hidden('sort', sort), )
