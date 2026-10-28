"""Crispy form buttons: classes from the layered button class table, rendered through the form-button leaf.

In a crispy ``Layout`` (e.g. ``FormActions``) a button renders as one ``<button>`` through
``crud_views/tags/button/form.html`` (Phase 6). Its value, label, name, id and attributes are literal text, never
template code. Added with ``helper.add_input()`` it stays a crispy input, rendered by the template pack.
"""

from crispy_forms import layout
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import render_to_string

from crud_views.lib.button_classes import get_button_class

FORM_LEAF_TEMPLATE = "crud_views/tags/button/form.html"


class _TableClassMixin:
    """
    Sets the crispy ``field_classes`` of the instance from the button class table, before crispy
    appends a project supplied ``css_class``. ``slot`` (``"location:slot"``) picks the table key.

    On the layout path ``render()`` replaces crispy's: it never renders the value as a template and gives the
    selected template only the normalized form-button data (``FORM_LEAF_KEYS``), no ``input`` object.
    """

    slot: str
    # the bundled leaf; a subclass ``template`` or an explicit ``template=`` argument wins (``%s`` is the pack)
    template = FORM_LEAF_TEMPLATE

    def __init__(self, name, value, *, slot: str | None = None, **kwargs):
        self._cv_slot = slot or self.slot
        self.field_classes = get_button_class(*self._cv_slot.split(":", 1))
        self._cv_css_id = kwargs.get("css_id")
        self._cv_css_class = kwargs.get("css_class")
        self._cv_attrs = {k: v for k, v in kwargs.items() if k not in ("css_id", "css_class", "template")}
        super().__init__(name, value, **kwargs)

    def _cv_form_kind(self) -> str:
        """The semantic form kind of the slot: ``form:<FORM_KINDS member>``, else ValueError (layout path only)."""
        from crud_views.lib.button_classes import FORM_KINDS

        location, _, kind = self._cv_slot.partition(":")
        if location != "form" or kind not in FORM_KINDS:
            raise ValueError(
                f"{type(self).__name__} slot must be 'form:<kind>' with a kind of {sorted(FORM_KINDS)} to render in"
                f" a layout, got {self._cv_slot!r}"
            )
        return kind

    def _cv_button_context(self) -> dict:
        """The raw form-button data this button hands to ``cv_button_data(ctx, "form")``."""
        return {
            "cv_key": self._cv_form_kind(),
            "cv_type": self.input_type,
            "cv_name": self.name,
            "cv_value": self.value,
            "cv_id": self.id,
            "cv_css_id": self._cv_css_id,
            "cv_css_class": self._cv_css_class,
            "cv_attrs": dict(self._cv_attrs),
        }

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        # deferred: crud_views.lib.view needs the app registry, and this module is imported by public form modules
        # (e.g. crud_views_workflow.lib) before django.setup()
        from crud_views.lib.view.button_data import cv_button_data

        data = cv_button_data(self._cv_button_context(), "form")
        return render_to_string(self.get_template_name(template_pack), data)


class Submit(_TableClassMixin, layout.Submit):
    slot = "form:submit"


class Button(_TableClassMixin, layout.Button):
    slot = "form:cancel"


class Reset(_TableClassMixin, layout.Reset):
    slot = "form:filter-reset"
