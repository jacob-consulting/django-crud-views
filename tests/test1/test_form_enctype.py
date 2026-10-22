"""Each form content template posts as multipart/form-data, so file fields upload (#236)."""

import re

import pytest
from django import forms
from django.template.loader import render_to_string
from django.test import RequestFactory


class UploadForm(forms.Form):
    attachment = forms.FileField()


@pytest.mark.parametrize(
    "template",
    [
        "crud_views/view_create.content.html",
        "crud_views/view_update.content.html",
        "crud_views/view_custom_form.content.html",
    ],
)
def test_form_content_template_posts_multipart(template):
    request = RequestFactory().get("/")
    html = render_to_string(template, {"form": UploadForm(), "request": request, "view": None}, request=request)
    # crispy renders its own <form> inside, which a browser ignores: only the outermost tag decides the encoding
    outer_form_tag = re.search(r"<form\b[^>]*>", html).group(0)
    assert 'enctype="multipart/form-data"' in outer_form_tag
