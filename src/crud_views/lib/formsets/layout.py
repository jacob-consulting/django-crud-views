from __future__ import annotations

from crispy_forms.layout import LayoutObject
from django.template.loader import render_to_string


class Formsets(LayoutObject):
    template = "crud_views/formsets/formsets.html"

    def render(self, form, context, **kwargs):
        # deferred: keeps the import of this module free of the crispy adapters and their dependencies
        from crud_views.lib.crispy.buttons import _CV_PAGE_OWNER, _cv_page_tier

        # a scoped copy: the caller's context is not touched. flatten() merges the page with the enclosing helper
        # overlay, so the page owner of the form buttons in the rows is captured before and carried privately
        data = context.flatten()
        data["formsets"] = context.get("formsets")
        data[_CV_PAGE_OWNER] = _cv_page_tier(context)
        return render_to_string(self.template, data)


class FormControl(LayoutObject):
    template = "crud_views/formsets/control.html"

    def __init__(self, formset=None):
        self.formset = formset

    def render(self, form, context, **kwargs):
        context.update({"form": form, "formset": self.formset})
        return render_to_string(self.template, context.flatten())
