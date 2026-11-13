"""Database-backed native selectors, conditional authority and render coverage."""

import json
from unittest.mock import patch

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db.models import CharField, F, Value
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context
from django.test import Client, override_settings
from django.urls import path
from lxml import html

from crud_views.lib import conditional
from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupFormMixin, ToggleGroup
from crud_views.lib.formsets import FormSet, InlineFormSet
from tests.test1.app.models import Author, Profile, Publisher
from tests.test1.app.models import ConditionalPersistenceRecord as Record

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


def guard_form(source):
    """Server declaration plus explicit render guard is the complete integration."""

    class GuardForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [ConditionalGroup(source.when(), fields=[], required=[])]

        class Meta:
            model = Record
            fields = ["reference"]

        def __init__(self, *args, **kwargs):
            kwargs.pop("cv_view", None)
            super().__init__(*args, **kwargs)
            self.fields["reference"].queryset = Publisher.objects.annotate(category=F("name"))

        @property
        def helper(self):
            helper = FormHelper()
            helper.form_action = ""
            helper.disable_csrf = True
            helper.layout = Layout("reference", ToggleGroup(source.when()))
            return helper

    return GuardForm


@pytest.mark.parametrize("render_mode", ["base", "ordinary-inline"])
def test_queryset_no_fields_render_coverage(render_mode, django_assert_num_queries):
    known = Publisher.objects.create(name="general")
    source = source_for()

    def render(source, *, bound=False):
        klass = guard_form(source)
        if render_mode == "base":
            form = klass(data={"reference": str(known.pk)} if bound else None)
            return render_crispy_form(form)

        class Rows(InlineFormSet):
            def get_helper_layout_fields(self):
                # The controller stays outside the empty guard in ordinary inlines too.
                return ["reference", ToggleGroup(source.when())]

        factory = inlineformset_factory(Profile, Record, form=klass, formset=Rows, extra=1)
        data = {"records-TOTAL_FORMS": "1", "records-INITIAL_FORMS": "0", "records-0-reference": str(known.pk)}
        rows = factory(formset=FormSet(klass=factory, title="Records"), prefix="records", data=data if bound else None)
        return render_crispy_form(rows, helper=rows.helper)

    with django_assert_num_queries(0):
        form = guard_form(source)()
        guard = ToggleGroup(source.when())
    with django_assert_num_queries(1):
        context = Context()
        assert guard.render(form, context).strip() == ""
        assert ToggleGroup(source.when()).render(form, context).strip() == ""
    doc = html.fromstring(render(source))
    assert len(doc.cssselect("select")) == 1
    assert not doc.cssselect("[cv-data-toggle-group]")
    Publisher.objects.create(name="unconfigured")
    with pytest.raises(ImproperlyConfigured, match=r"reference.*unconfigured"):
        render(source)
    doc = html.fromstring(render(source, bound=True))
    assert "unconfigured" in doc.cssselect(".cv-queryset-condition-error")[0].text_content()
    assert not doc.cssselect("[cv-data-toggle-group]")
    assert "cv-queryset-condition-error" not in render(source_for(allow_unmatched=True))


def test_queryset_render_cache_is_local_and_rechecks_current_queryset(django_assert_num_queries):
    active = Publisher.objects.create(name="active")
    source = source_for()
    form = record_form(source)()
    first = ToggleGroup(source.when("active"))
    second = ToggleGroup(source.when("other"))
    with django_assert_num_queries(1):
        context = Context()
        assert str(active.pk) in first.render(form, context)
        second.render(form, context)
    Publisher.objects.filter(pk=active.pk).update(name="unknown")
    with pytest.raises(ImproperlyConfigured, match="unknown"), django_assert_num_queries(1):
        first.render(form, Context())
    form.fields["reference"].queryset = Publisher.objects.none()
    with django_assert_num_queries(0):
        first.render(form, context)


def test_queryset_bound_diagnostics_are_escaped_visible_and_preserve_errors():
    hostile = '<img src=x onerror="alert(1)">'
    unknown = Publisher.objects.create(name=hostile)
    source = source_for()
    form = record_form(source)(data={"reference": str(unknown.pk)})
    assert not form.is_valid()
    form.add_error(None, "inherited invariant")
    doc = html.fromstring(render_crispy_form(form))
    diagnostics = doc.cssselect(".cv-queryset-condition-error")
    assert len(diagnostics) == 2
    assert all(hostile in node.text_content() for node in diagnostics)
    assert all(not node.xpath("ancestor::*[@cv-data-toggle-group]") for node in diagnostics)
    assert not doc.cssselect("img, script, [onerror]")
    assert "inherited invariant" in doc.text_content()
    assert doc.cssselect("#error_1_id_reference")


def test_queryset_bound_siblings_and_untouched_extra_render_after_failure():
    unknown = Publisher.objects.create(name="unknown")
    known = Publisher.objects.create(name="general")
    klass = record_form(source_for())
    forms_to_render = [
        klass(data={"rows-0-reference": str(unknown.pk)}, prefix="rows-0"),
        klass(data={"rows-1-reference": str(known.pk)}, prefix="rows-1"),
        klass(data={}, prefix="rows-2", empty_permitted=True, use_required_attribute=False),
    ]
    assert not forms_to_render[0].is_valid()
    assert forms_to_render[1].is_valid()
    assert forms_to_render[2].is_valid()
    for form in forms_to_render:
        doc = html.fromstring(render_crispy_form(form))
        assert doc.cssselect(".cv-queryset-condition-error")
        assert doc.cssselect("select")[0].get("name") == form.add_prefix("reference")


def test_queryset_uuid_tokens_match_native_options():
    author = Author.objects.create(first_name="Native", last_name="UUID")
    source = source_for("author")

    class AuthorForm(ConditionalGroupFormMixin, forms.Form):
        author = forms.ModelChoiceField(queryset=Author.objects.annotate(category=Value("active")))
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(source.when("active"), ["detail"])]

    form = AuthorForm(data={"author": str(author.pk), "detail": "saved"})
    helper = FormHelper()
    helper.form_action = ""
    helper.disable_csrf = True
    helper.layout = Layout("author", ToggleGroup(source.when("active"), "detail"))
    assert form.is_valid(), form.errors
    doc = html.fromstring(render_crispy_form(form, helper=helper))
    token = doc.cssselect("select option[selected]")[0].get("value")
    assert token == str(author.pk)
    assert json.loads(doc.cssselect("[cv-data-toggle-group]")[0].get("cv-data-toggle-values")) == [token]


def test_queryset_dynamic_empty_metadata_and_no_extra_label_work():
    Publisher.objects.create(name="general")
    form = record_form(source_for())()
    field = form.fields["reference"]
    with patch.object(field, "label_from_instance", wraps=field.label_from_instance) as label:
        doc = html.fromstring(render_crispy_form(form))
    assert label.call_count == 1  # Native option label only; no metadata label access.
    for group in doc.cssselect("[cv-data-toggle-group]"):
        assert group.get("cv-data-toggle-kind") == "queryset"
        assert json.loads(group.get("cv-data-toggle-values")) == []


@pytest.mark.parametrize("category", [None, "", "missing", "unknown"])
@pytest.mark.parametrize("permissive", [False, True])
def test_queryset_empty_object_category_is_not_blank_selection(category, permissive):
    option = Publisher.objects.create(name="option")
    source = source_for(allow_unmatched=permissive)
    klass = record_form(source)
    queryset = Publisher.objects.all()
    if category != "missing":
        queryset = queryset.annotate(category=Value(category, output_field=CharField()))
    form = klass(data={"reference": str(option.pk), "blank_text": "discard"})
    form.fields["reference"].queryset = queryset
    assert form.is_valid() is permissive
    if not permissive:
        assert form.errors.as_data()["reference"][0].code == "unmatched_category"
    assert form.cleaned_data["blank_text"] == ""
    blank = klass(data={"reference": ""})
    blank.fields["reference"].queryset = queryset
    assert blank.is_valid()
    unbound = klass()
    unbound.fields["reference"].queryset = queryset
    if permissive:
        assert "cv-queryset-condition-error" not in render_crispy_form(unbound)
    else:
        with pytest.raises(ImproperlyConfigured, match=r"reference.*category"):
            render_crispy_form(unbound)


def test_queryset_unoffered_categories_are_not_scanned():
    Publisher.objects.create(name="unknown")
    general = Publisher.objects.create(name="general")
    form = record_form(source_for())()
    form.fields["reference"].queryset = form.fields["reference"].queryset.filter(pk=general.pk)
    doc = html.fromstring(render_crispy_form(form))
    assert len(doc.cssselect("select option")) == 2  # Placeholder plus the offered object.


def test_queryset_metadata_escapes_native_text_tokens_and_hostile_category():
    token = '"><script>alert("token")</script>'
    category = '<img src=x onerror="category">'
    option = Record.objects.create(parent=Profile.objects.create(name="parent"), unique_text=token)
    source = conditional.QuerysetConditions("choice", conditional_key="category", keys=[category])

    class TextKeyForm(ConditionalGroupFormMixin, forms.Form):
        choice = forms.ModelChoiceField(
            queryset=Record.objects.annotate(category=Value(category)), to_field_name="unique_text"
        )
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(source.when(category), ["detail"])]

    form = TextKeyForm(data={"choice": token, "detail": "kept"})
    helper = FormHelper()
    helper.form_action = ""
    helper.disable_csrf = True
    helper.layout = Layout("choice", ToggleGroup(source.when(category), "detail", legend="Details"))
    assert form.is_valid(), form.errors
    assert form.cleaned_data["choice"].pk == option.pk
    doc = html.fromstring(render_crispy_form(form, helper=helper))
    assert doc.cssselect("option[selected]")[0].get("value") == token
    assert json.loads(doc.cssselect("fieldset")[0].get("cv-data-toggle-values")) == [token]
    assert not doc.cssselect("script, img, [onerror]")


def test_queryset_guard_and_visible_group_share_projection(django_assert_num_queries):
    Publisher.objects.create(name="active")
    source = source_for()
    form = record_form(source)()
    context = Context()
    with django_assert_num_queries(1):
        assert ToggleGroup(source.when()).render(form, context).strip() == ""
        ToggleGroup(source.when("active")).render(form, context)
