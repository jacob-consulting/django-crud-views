"""Each form content template emits a widget's Media exactly once (#191)."""

import pytest
from django import forms
from django.template.loader import render_to_string
from django.test import RequestFactory


class ProbeWidget(forms.TextInput):
    class Media:
        js = ("probe/probe.js",)
        css = {"all": ("probe/probe.css",)}


class ProbeForm(forms.Form):
    x = forms.CharField(widget=ProbeWidget)


@pytest.mark.parametrize(
    "template",
    [
        "crud_views/view_create.content.html",
        "crud_views/view_update.content.html",
        "crud_views/view_custom_form.content.html",
    ],
)
def test_form_content_template_renders_widget_media_once(template):
    request = RequestFactory().get("/")
    html = render_to_string(template, {"form": ProbeForm(), "request": request, "view": None}, request=request)
    assert html.count("probe/probe.js") == 1
    assert html.count("probe/probe.css") == 1
