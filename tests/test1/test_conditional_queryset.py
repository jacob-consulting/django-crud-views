"""Database-backed native selectors, conditional authority and render coverage."""

import json
from pathlib import Path

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.test import Client, override_settings
from django.urls import path
from lxml import html

import crud_views
from crud_views.lib import conditional
from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupFormMixin, ToggleGroup
from tests.test1.app.models import ConditionalPersistenceRecord as Record
from tests.test1.app.models import Profile, Publisher

pytestmark = pytest.mark.django_db


def source_for(controller="reference", **kwargs):
    factory = getattr(conditional, "QuerysetConditions", None)
    assert factory is not None, "QuerysetConditions must expose native queryset/category conditions"
    return factory(controller, conditional_key="category", keys=("active", "other", "general"), **kwargs)


def record_form(source):
    class RecordForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(source.when("active"), ["blank_text"]),
            ConditionalGroup(source.when("other"), ["nullable_text"]),
        ]

        class Meta:
            model = Record
            fields = ["reference", "blank_text", "nullable_text"]

        def __init__(self, *args, **kwargs):
            kwargs.pop("cv_view", None)
            super().__init__(*args, **kwargs)
            self.fields["reference"].queryset = Publisher.objects.annotate(category=F("name"))

        @property
        def helper(self):
            helper = FormHelper()
            helper.form_action = ""
            helper.disable_csrf = True
            helper.layout = Layout(
                "reference",
                ToggleGroup(source.when("active"), "blank_text"),
                ToggleGroup(source.when("other"), "nullable_text"),
            )
            return helper

    return RecordForm


def test_queryset_render_save_reopen():
    assert Path(crud_views.__file__).resolve().is_relative_to(Path.cwd() / "src")
    active = Publisher.objects.create(name="active")
    general = Publisher.objects.create(name="general")
    record = Record.objects.create(parent=Profile.objects.create(name="parent"), blank_text="")
    form_class = record_form(source_for())

    def editor(request):
        form = form_class(
            data=request.POST if request.method == "POST" else None,
            instance=Record.objects.get(pk=record.pk),
        )
        if request.method == "POST" and form.is_valid():
            form.save()
            return HttpResponseRedirect("/")
        return HttpResponse(render_crispy_form(form))

    with override_settings(ROOT_URLCONF=type("URLs", (), {"urlpatterns": [path("", editor)]})):
        client = Client()
        doc = html.fromstring(client.get("/").content)
        options = {node.text: node.get("value") for node in doc.cssselect("select[name=reference] option")}
        assert options["active"] == str(active.pk)
        assert options["general"] == str(general.pk)
        groups = doc.cssselect("[cv-data-toggle-group]")
        assert json.loads(groups[0].get("cv-data-toggle-values")) == [options["active"]]
        response = client.post("/", {"reference": options["active"], "blank_text": "saved", "nullable_text": "junk"})
        assert response.status_code == 302, response.content
        record.refresh_from_db()
        assert record.blank_text == "saved"
        assert record.nullable_text is None
        response = client.post("/", {"reference": options["general"], "blank_text": "forged"})
        assert response.status_code == 302, response.content
        record.refresh_from_db()
        assert record.reference_id == general.pk
        assert record.blank_text == ""
        doc = html.fromstring(client.get("/").content)
        assert doc.cssselect("input[name=blank_text]")[0].get("value", "") == ""
        assert doc.cssselect("select[name=reference] option[selected]")[0].get("value") == str(general.pk)


@pytest.mark.parametrize("data", [{}, {"reference": ""}, {"reference": "99999"}])
def test_queryset_missing_controller_never_activates(data):
    form = record_form(source_for())(data={**data, "blank_text": "discard", "nullable_text": "discard"})
    form.is_valid()
    assert form.cleaned_data["blank_text"] == ""
    assert form.cleaned_data["nullable_text"] is None


def test_queryset_rejects_unmatched_selection_without_get():
    unknown = Publisher.objects.create(name="unknown")
    record = Record.objects.create(parent=Profile.objects.create(name="parent"), blank_text="original")
    form = record_form(source_for())(data={"reference": str(unknown.pk), "blank_text": "forged"}, instance=record)
    assert not form.is_valid()
    assert "unknown" in str(form.errors["reference"])
    with pytest.raises(ValueError):
        form.save()
    record.refresh_from_db()
    assert record.blank_text == "original"
