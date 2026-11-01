"""Real model and inline-tree persistence for inactive conditional groups."""

import datetime
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms.models import inlineformset_factory
from django.test import RequestFactory

from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from tests.test1.app.models import ConditionalPersistenceRecord as Record
from tests.test1.app.models import Profile, Publisher

pytestmark = pytest.mark.django_db


def record_form(names, *, empty_values=None, disabled=()):
    class RecordForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), list(names), empty_values=empty_values)]

        class Meta:
            model = Record
            fields = ["active", *names]

        def __init__(self, *args, **kwargs):
            kwargs.pop("cv_view", None)
            super().__init__(*args, **kwargs)
            for name in disabled:
                self.fields[name].disabled = True

    return RecordForm


def inline_tree(row, form_class, payload=None, files=None, *, extra=0):
    klass = inlineformset_factory(Profile, Record, form=form_class, formset=InlineFormSet, extra=extra)
    trees = FormSets(formsets={"records": FormSet(title="Records", klass=klass)})
    prefix = f"records-{row.parent_id}-0"
    post = {
        f"{prefix}-TOTAL_FORMS": str(1 + extra),
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": str(row.pk),
        **{f"{prefix}-0-{key}": value for key, value in (payload or {}).items()},
    }
    request = RequestFactory().post("/", post)
    if files:
        request.FILES.update({f"{prefix}-0-{key}": value for key, value in files.items()})
    main = forms.modelform_factory(Profile, fields=[])(instance=row.parent)
    trees.init(request, main)
    return trees, trees.x_formsets[0].instance.forms[0]


@pytest.fixture
def row():
    return Record.objects.create(parent=Profile.objects.create(name="parent"))


@pytest.mark.parametrize("posted", [{}, {"blank_text": ""}, {"blank_text": "forged"}])
def test_omitted_empty_and_forged_defaults_persist(row, posted):
    row.nullable_text = "old"
    row.blank_text = "old"
    row.save()
    form = record_form(["nullable_text", "blank_text"])(instance=row, data=posted)
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert row.nullable_text is None
    assert row.blank_text == ""


@pytest.mark.parametrize(
    ("name", "initial", "empty"),
    [
        ("flag", True, False),
        ("nullable_flag", True, None),
        ("number", 25, None),
        ("decimal", Decimal("1.23"), None),
        ("date", datetime.date(2026, 1, 2), None),
        ("time", datetime.time(12, 30), None),
        ("timestamp", datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC), None),
        ("duration", datetime.timedelta(seconds=30), None),
        ("token", uuid.UUID("12345678-1234-1234-1234-123456789abc"), None),
    ],
)
def test_scalar_matrix_refreshes_final_empty(row, name, initial, empty):
    setattr(row, name, initial)
    row.save()
    form = record_form([name])(instance=row, data={name: "forged"})
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert getattr(row, name) == empty


def test_nullable_relation_clears(row):
    row.reference = Publisher.objects.create(name="reference")
    row.save()
    form = record_form(["reference"])(instance=row, data={"reference": "invalid"})
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert row.reference_id is None


@pytest.mark.parametrize("data", [{}, {"blank_text": "forged"}])
def test_disabled_scalar_wins_over_explicit_override(row, data):
    form = record_form(["blank_text"], empty_values={"blank_text": ""}, disabled=["blank_text"])(
        instance=row, data=data
    )
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert row.blank_text == "default text"


def test_disabled_validation_errors_survive_off_group(row):
    form = record_form(["blank_text"], disabled=["blank_text"])(instance=row, data={})
    form.fields["blank_text"].validators.append(lambda value: (_ for _ in ()).throw(ValidationError("trusted invalid")))
    assert not form.is_valid()
    assert "trusted invalid" in str(form.errors["blank_text"])


def test_model_clean_sees_final_state_and_blocks_persistence(row, monkeypatch):
    observed = []

    def clean(instance):
        observed.append(instance.blank_text)
        if instance.blank_text == "":
            raise ValidationError("invariant")

    monkeypatch.setattr(Record, "clean", clean)
    form = record_form(["blank_text"])(instance=row, data={})
    assert not form.is_valid()
    assert observed == [""]
    assert "invariant" in str(form.non_field_errors())
    with pytest.raises(ValueError):
        form.save()
    row.refresh_from_db()
    assert row.blank_text == "default text"


def test_active_group_retains_ordinary_validation_and_value(row):
    form = record_form(["blank_text"])(instance=row, data={"active": "on", "blank_text": "edited"})
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert row.blank_text == "edited"


def test_unchanged_inline_scalar_reaches_real_tree_save(row):
    trees, form = inline_tree(row, record_form(["blank_text"]), {"blank_text": row.blank_text})
    assert trees.all_valid()
    assert not form.has_changed()
    original_save = Record.save
    with patch.object(Record, "save", autospec=True, side_effect=original_save) as save:
        trees.save()
    assert save.call_count == 1
    row.refresh_from_db()
    assert row.blank_text == ""
    assert Record.objects.count() == 1


def test_plain_form_defaults_and_explicit_falsy_values():
    class Plain(ConditionalGroupFormMixin, forms.Form):
        active = forms.BooleanField(required=False)
        text = forms.CharField(empty_value="")
        choices = forms.MultipleChoiceField(choices=[("a", "A")])
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["text", "choices"])]

    form = Plain(data={"text": "forged", "choices": ["a"]})
    assert form.is_valid()
    assert form.cleaned_data["text"] == ""
    assert form.cleaned_data["choices"] == []


def test_unsupported_custom_field_requires_explicit_value():
    class Custom(forms.CharField):
        pass

    class Plain(ConditionalGroupFormMixin, forms.Form):
        active = forms.BooleanField(required=False)
        text = Custom()
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["text"])]

    with pytest.raises(ImproperlyConfigured, match="active.*text"):
        Plain(data={}).is_valid()
    Plain.cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["text"], empty_values={"text": ""})]
    form = Plain(data={})
    assert form.is_valid()
    assert form.cleaned_data["text"] == ""
