import copy
import functools
from collections.abc import Iterable

from crispy_forms import layout
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.utils import TEMPLATE_PACK
from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.crispy.buttons import _CV_HELPER_OWNER, Reset, Submit
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


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
    cv_icon_action = "list"

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


class _PreparedLayout(layout.Layout):
    """A filter helper's private instance layout: always truthy, so crispy dispatches ``render_layout`` even when
    the selected layout is empty (crispy only renders a layout ``if helper and helper.layout``)."""

    def __bool__(self):
        return True


@functools.cache
def _prepared_layout_class(cls: type) -> type:
    """The always-truthy variant of a layout class; a custom layout keeps its own class behavior."""
    if issubclass(cls, _PreparedLayout) or getattr(cls, "_cv_prepared_layout", False):
        return cls
    if cls is layout.Layout:
        return _PreparedLayout
    return type(f"_Prepared{cls.__name__}", (cls,), {"__bool__": _PreparedLayout.__bool__, "_cv_prepared_layout": True})


class ListViewFilterFormHelper(FormHelper):
    """
    Form helper for the filter form

    A subclass declares only its filter fields in a class-level ``layout``; the helper appends the
    ``get_form_actions()`` group (Apply / Reset) after them, exactly once per selected layout. Each instance renders
    a private deep copy of the declared (or later assigned) layout, so the class layout, a caller's layout object
    and other instances are never changed. Without a layout the actual form's fields are rendered, then the actions.

    The hidden sort / order / direction controls stay crispy inputs (``add_input``) and render in the template
    pack's trailing inputs wrapper, after the visible actions. Controls a subclass adds with ``add_input()`` stay
    inputs too.
    """

    form_method = "GET"  # filter parameters are always GET
    form_tag = False

    # private lifecycle state (underscore: crispy's get_attributes never publishes it into the template context)
    _cv_prepared = None  # the instance layout currently selected and isolated
    _cv_default_fields = False  # True: no layout was selected, render the actual form's fields
    _cv_actions_layout = None  # the prepared layout the action group was resolved for
    _cv_actions = None  # that group (None: omitted)

    def __init__(self, view, request, form=None):
        # crispy replaces any layout with all form fields when its initializer receives the form: never pass it
        super().__init__()
        self._cv_prepare_layout()
        if form is not None:
            self.form = form

        self.view = view

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

    def get_form_actions(self) -> FormActions | None:
        """The visible filter actions, appended once after the filter fields; None omits the action group.

        An empty ``FormActions()`` is kept as an explicit, empty group.
        """
        return FormActions(
            Submit("submit", _("Apply Filter"), css_id="filter-button", slot="form:filter-submit"),
            Reset("reset", _("Reset Filter"), css_id="filter-button-reset"),
        )

    def __bool__(self):
        # FormHelper.__len__ counts the layout fields: an empty helper would skip render_layout altogether
        return True

    def _cv_prepare_layout(self):
        """Select and isolate the current layout (idempotent); returns the prepared instance layout.

        ``self.layout`` that is not the prepared instance was assigned by the caller (or is the class layout): it is
        deep-copied into a private, always-truthy instance layout, keeping its fields, order and nested or custom
        layout objects. An explicitly empty layout stays empty; only ``None`` (no layout) renders the form's fields.
        """
        current = self.layout
        if self._cv_prepared is not None and current is self._cv_prepared:
            return current
        if current is None:
            prepared = _PreparedLayout()
            self._cv_default_fields = True
        else:
            prepared = copy.deepcopy(current)
            prepared.__class__ = _prepared_layout_class(type(current))
            self._cv_default_fields = False
        # a new prepared layout: render_layout resolves its action group once (identity, not a lifetime flag)
        self._cv_prepared = prepared
        self.layout = prepared
        return prepared

    def get_attributes(self, template_pack=TEMPLATE_PACK):
        # crispy calls this before its `if helper and helper.layout` guard: prepare a replaced layout first
        self._cv_prepare_layout()
        return super().get_attributes(template_pack=template_pack)

    def render_layout(self, form, context, template_pack=TEMPLATE_PACK):
        prepared = self._cv_prepare_layout()
        if self._cv_actions_layout is not prepared:
            # exactly once per prepared layout
            self._cv_actions_layout = prepared
            self._cv_actions = self.get_form_actions()
            if self._cv_actions is not None and not self._cv_default_fields:
                prepared.fields.append(self._cv_actions)
        if self._cv_default_fields:
            # no selected layout: the actual form's fields, then the actions
            prepared.fields[:] = [*form.fields, *([] if self._cv_actions is None else [self._cv_actions])]
        # the actual helper owner of this invocation's buttons, for the duration of this render only
        with context.push({_CV_HELPER_OWNER: getattr(self, "view", None)}):
            return super().render_layout(form, context, template_pack=template_pack)
