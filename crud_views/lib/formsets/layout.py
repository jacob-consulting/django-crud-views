from __future__ import annotations

from crispy_forms.layout import LayoutObject
from django.template.loader import render_to_string


class Formsets(LayoutObject):
    template = "crud_views/formsets/formsets.html"

    def render(self, form, context, **kwargs):
        formsets = context.get("formsets")
        context.update({
            "formsets": formsets,
        })
        return render_to_string(self.template, context.flatten())


class FormControl(LayoutObject):
    template = "crud_views/formsets/control.html"

    def __init__(self, formset=None):
        self.formset = formset

    def render(self, form, context, **kwargs):
        context.update({
            "form": form,
            "formset": self.formset
        })
        return render_to_string(self.template, context.flatten())
