from __future__ import annotations

from crispy_forms.layout import Layout, LayoutObject
from django.template.loader import render_to_string


class ToggleGroup(LayoutObject):
    """Crispy layout wrapper for a conditional field-group.

    Renders the wrapped fields inside a marker div that ``toggle.js`` keys off.
    Cosmetic only — validation/clearing is enforced server-side by
    ``ConditionalGroupFormMixin``.
    """

    template = "crud_views/conditional/toggle_group.html"

    def __init__(self, toggle_field: str, *fields, css_class: str | None = None):
        self.toggle_field = toggle_field
        self.css_class = css_class
        self.inner = Layout(*fields)

    def render(self, form, context, **kwargs):
        inner_html = self.inner.render(form, context, **kwargs)
        context.update(
            {
                "cv_toggle_field": self.toggle_field,
                "cv_toggle_css": self.css_class or "",
                "cv_toggle_inner": inner_html,
            }
        )
        return render_to_string(self.template, context.flatten())
