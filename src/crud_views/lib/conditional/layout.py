from __future__ import annotations

import json

from crispy_forms.layout import Layout, LayoutObject
from django.template.loader import render_to_string

from .queryset import QuerysetConditionCoverageError, _QuerysetToggle
from .toggle import ToggleSource, ValueToggle


class ToggleGroup(LayoutObject):
    """Crispy layout wrapper for a conditional field-group.

    Renders the wrapped fields inside a marker element that ``toggle.js`` keys
    off. Pass ``legend=`` to render a titled ``<fieldset>`` instead of a bare
    ``<div>``; the marker sits on the fieldset so the whole group (legend
    included) hides when the toggle is off. Cosmetic only — validation/clearing
    is enforced server-side by ``ConditionalGroupFormMixin``.
    """

    template = "crud_views/conditional/toggle_group.html"

    def __init__(
        self, toggle_field: str | ToggleSource, *fields, css_class: str | None = None, legend: str | None = None
    ):
        self.toggle_field = toggle_field
        self.css_class = css_class
        self.legend = legend
        self.inner = Layout(*fields)

    def render(self, form, context, **kwargs):
        values = None
        diagnostic = ""
        queryset_toggle = isinstance(self.toggle_field, _QuerysetToggle)
        guard = queryset_toggle and not self.toggle_field.values and not self.inner.fields
        if queryset_toggle:
            try:
                values = self.toggle_field.render_values(form, context)
            except QuerysetConditionCoverageError as exc:
                if not form.is_bound:
                    raise
                # Rendering must preserve validation errors, including valid
                # sibling/empty rows on a rejected bound formset response.
                diagnostic = str(exc)
                values = []
        elif isinstance(self.toggle_field, ValueToggle):
            values = self.toggle_field.values
        inner_html = self.inner.render(form, context, **kwargs)
        name = self.toggle_field.field_name() if isinstance(self.toggle_field, ToggleSource) else self.toggle_field
        context.update(
            {
                "cv_toggle_field": form.add_prefix(name),
                "cv_toggle_values": json.dumps(values) if values is not None else None,
                "cv_toggle_kind": "queryset" if queryset_toggle else "",
                "cv_toggle_diagnostic": diagnostic,
                "cv_toggle_guard": guard,
                "cv_toggle_css": self.css_class or "",
                "cv_toggle_legend": self.legend or "",
                "cv_toggle_inner": inner_html,
            }
        )
        return render_to_string(self.template, context.flatten())
