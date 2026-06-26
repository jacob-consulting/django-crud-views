# tests/test1/test_conditional_layout.py
import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row
from crispy_forms.utils import render_crispy_form
from django import forms

from crud_views.lib.conditional.layout import ToggleGroup
from crud_views.lib.crispy import Column6
from tests.test1.app.models import Profile

pytestmark = pytest.mark.django_db


class _LayoutForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        h = FormHelper()
        h.layout = Layout(
            Row(Column6("name"), Column6("with_contact")),
            ToggleGroup("with_contact", Row(Column6("email"), Column6("phone"))),
        )
        return h


def test_toggle_group_renders_marker_attributes():
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert 'cv-data-toggle-field="with_contact"' in html
    assert "cv-toggle-group" in html
    assert "email" in html and "phone" in html


def test_toggle_group_includes_toggle_js():
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "crud_views/js/toggle.js" in html
