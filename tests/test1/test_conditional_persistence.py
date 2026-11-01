"""Real model and inline-tree persistence for inactive conditional groups."""

import datetime
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django import forms
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import inlineformset_factory
from django.test import RequestFactory, override_settings
from django.test.utils import isolate_apps

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


def test_declared_disabled_required_field_retains_native_error():
    class Plain(ConditionalGroupFormMixin, forms.Form):
        active = forms.BooleanField(required=False)
        protected = forms.CharField(disabled=True)
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["protected"])]

    form = Plain(data={"protected": "forged"})
    assert not form.is_valid()
    assert form.errors["protected"] == ["This field is required."]


def test_inherited_form_nonfield_error_is_not_suppressed(row):
    class InvariantForm(forms.ModelForm):
        class Meta:
            model = Record
            fields = ["active", "blank_text"]

        def clean(self):
            cleaned = super().clean()
            self.add_error(None, "inherited invariant")
            return cleaned

    class Conditional(ConditionalGroupFormMixin, InvariantForm):
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["blank_text"])]

    form = Conditional(instance=row, data={"blank_text": "forged"})
    assert not form.is_valid()
    assert "inherited invariant" in str(form.non_field_errors())
    with pytest.raises(ValueError):
        form.save()
    row.refresh_from_db()
    assert row.blank_text == "default text"


def test_model_uniqueness_validation_is_retained(row):
    Record.objects.create(parent=row.parent, unique_text="reserved")
    form = record_form(["unique_text"], empty_values={"unique_text": "reserved"})(instance=row, data={})
    assert not form.is_valid()
    assert "already exists" in str(form.errors["unique_text"])
    row.refresh_from_db()
    assert row.unique_text is None


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

    with pytest.raises(ImproperlyConfigured, match=r"active.*text"):
        Plain(data={}).is_valid()
    Plain.cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["text"], empty_values={"text": ""})]
    form = Plain(data={})
    assert form.is_valid()
    assert form.cleaned_data["text"] == ""


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    # ImageField references deliberately require neither uploaded image bytes nor Pillow.
    with override_settings(MEDIA_ROOT=tmp_path):
        stores = {}
        for name in ("attachment", "image"):
            storage = FileSystemStorage(location=tmp_path / name)
            monkeypatch.setattr(Record._meta.get_field(name), "storage", storage)
            stores[name] = storage
        yield stores
    # pytest's tmp_path cleanup owns fixture content; product save has no cleanup policy.


def seed_reference(row, name, storage):
    stored = storage.save("original.bin", ContentFile(b"original fixture content"))
    setattr(row, name, stored)
    row.save()
    return stored


@pytest.mark.parametrize("name", ["attachment", "image"])
def test_unchanged_inline_file_reference_clears_without_deleting_content(row, isolated_storage, name):
    storage = isolated_storage[name]
    stored = seed_reference(row, name, storage)
    trees, form = inline_tree(row, record_form([name]), extra=1)
    assert trees.all_valid()
    assert not form.has_changed()
    assert not trees.x_formsets[0].instance.forms[1].has_changed()
    original_save = Record.save
    with (
        patch.object(storage, "delete", wraps=storage.delete) as delete,
        patch.object(storage, "save", wraps=storage.save) as write,
        patch.object(Record, "save", autospec=True, side_effect=original_save) as save,
    ):
        trees.save()
        assert save.call_count == 1
        delete.assert_not_called()
        write.assert_not_called()
    row.refresh_from_db()
    assert getattr(row, name).name == ""
    assert storage.exists(stored)
    with storage.open(stored, "rb") as content:
        assert content.read() == b"original fixture content"
    assert Record.objects.count() == 1


@pytest.mark.parametrize("name", ["attachment", "image"])
@pytest.mark.parametrize("mode", ["disabled", "explicit-none", "already-empty"])
def test_file_no_change_controls_do_not_force_save(row, isolated_storage, name, mode):
    storage = isolated_storage[name]
    stored = "" if mode == "already-empty" else seed_reference(row, name, storage)
    form_class = record_form(
        [name],
        empty_values={name: None} if mode == "explicit-none" else {name: False},
        disabled=[name] if mode == "disabled" else [],
    )
    trees, form = inline_tree(row, form_class, extra=1)
    if name == "image" and mode == "disabled":
        # Native ImageField validates a nonempty disabled initial through Pillow.
        # This reference-only fixture supplies native None/no-change instead:
        # the model still holds its real stored ImageFieldFile reference.
        form.initial[name] = None
        assert type(form.fields[name]) is forms.ImageField
        assert row.image.name == stored
    assert trees.all_valid()
    assert not form.has_changed()
    with patch.object(Record, "save", autospec=True) as save, patch.object(storage, "delete") as delete:
        trees.save()
        save.assert_not_called()
        delete.assert_not_called()
    row.refresh_from_db()
    assert getattr(row, name).name == stored
    if stored:
        assert storage.exists(stored)
    assert Record.objects.count() == 1


@pytest.mark.parametrize("disabled", [False, True])
def test_received_off_file_upload_is_discarded_with_no_storage_write(row, isolated_storage, disabled):
    storage = isolated_storage["attachment"]
    stored = seed_reference(row, "attachment", storage)
    upload = SimpleUploadedFile("forged-upload.txt", b"untrusted received upload")
    trees, form = inline_tree(
        row,
        record_form(["attachment"], empty_values={"attachment": False}, disabled=["attachment"] if disabled else []),
        files={"attachment": upload},
    )
    assert form.files[form.add_prefix("attachment")].read() == b"untrusted received upload"
    with patch.object(storage, "save", wraps=storage.save) as write, patch.object(storage, "delete") as delete:
        assert trees.all_valid()
        trees.save()
        write.assert_not_called()
        delete.assert_not_called()
    row.refresh_from_db()
    assert row.attachment.name == (stored if disabled else "")
    assert storage.exists(stored)
    assert not storage.exists("conditional/forged-upload.txt")
    assert storage.listdir("")[1] == [stored]


@pytest.mark.parametrize("empty_values", [None, {"tags": []}])
def test_unchanged_inline_relation_uses_native_save_m2m(row, empty_values):
    tag = Publisher.objects.create(name="tag")
    row.tags.add(tag)
    trees, form = inline_tree(row, record_form(["tags"], empty_values=empty_values), {"tags": [str(tag.pk)]}, extra=1)
    assert trees.all_valid()
    assert not form.has_changed()
    original_save = Record.save
    with patch.object(Record, "save", autospec=True, side_effect=original_save) as save:
        trees.save()
        assert save.call_count == 1
    row.refresh_from_db()
    assert list(row.tags.all()) == []
    assert Record.objects.count() == 1


@pytest.mark.parametrize("posted", [{}, {"tags": ["999999"]}])
def test_disabled_relation_retains_trusted_values_before_override(row, posted):
    tag = Publisher.objects.create(name="trusted tag")
    row.tags.add(tag)
    trees, form = inline_tree(row, record_form(["tags"], empty_values={"tags": []}, disabled=["tags"]), posted)
    assert trees.all_valid()
    assert not form.has_changed()
    with patch.object(Record, "save", autospec=True) as save:
        trees.save()
        save.assert_not_called()
    row.refresh_from_db()
    assert list(row.tags.all()) == [tag]


@pytest.mark.parametrize("empty", [False, "", None])
def test_explicit_file_values_keep_native_false_empty_string_none_meanings(row, isolated_storage, empty):
    storage = isolated_storage["attachment"]
    stored = seed_reference(row, "attachment", storage)
    form = record_form(["attachment"], empty_values={"attachment": empty})(instance=row, data={})
    with patch.object(storage, "delete") as delete:
        assert form.is_valid(), form.errors
        form.save()
        delete.assert_not_called()
    row.refresh_from_db()
    assert row.attachment.name == (stored if empty is None else "")
    assert storage.exists(stored)


@pytest.mark.parametrize("empty", [False, "", None])
def test_explicit_scalar_falsy_values_are_not_reinterpreted(row, empty):
    name = "flag" if empty is False else "nullable_text"
    form = record_form([name], empty_values={name: empty})(instance=row, data={})
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert getattr(row, name) == empty


def test_explicit_m2m_empty_collection_uses_commit_false_then_save_m2m(row):
    tag = Publisher.objects.create(name="tag")
    row.tags.add(tag)
    form = record_form(["tags"], empty_values={"tags": []})(instance=row, data={})
    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    assert list(row.tags.all()) == [tag]
    instance.save()
    form.save_m2m()
    row.refresh_from_db()
    assert list(row.tags.all()) == []


def test_already_empty_relation_does_not_force_existing_save(row):
    trees, form = inline_tree(row, record_form(["tags"]), extra=1)
    assert trees.all_valid()
    assert not form.has_changed()
    with patch.object(Record, "save", autospec=True) as save:
        trees.save()
        save.assert_not_called()
    assert Record.objects.count() == 1


def test_revalidation_keeps_the_persisted_change_until_saved(row):
    trees, form = inline_tree(row, record_form(["blank_text"]), {"blank_text": row.blank_text})
    assert trees.all_valid()
    form.full_clean()
    assert form.is_valid()
    assert not form.has_changed()
    trees.save()
    row.refresh_from_db()
    assert row.blank_text == ""


@pytest.mark.parametrize("data", [{}, {"reference": "999999"}])
def test_disabled_foreign_key_keeps_trusted_value(row, data):
    reference = Publisher.objects.create(name="trusted")
    row.reference = reference
    row.save()
    form = record_form(["reference"], empty_values={"reference": None}, disabled=["reference"])(instance=row, data=data)
    assert form.is_valid(), form.errors
    form.save()
    row.refresh_from_db()
    assert row.reference == reference


def test_file_clearing_cannot_bypass_model_invariant(row, isolated_storage, monkeypatch):
    storage = isolated_storage["attachment"]
    stored = seed_reference(row, "attachment", storage)

    def clean(instance):
        if not instance.attachment:
            raise ValidationError("file invariant")

    monkeypatch.setattr(Record, "clean", clean)
    trees, form = inline_tree(row, record_form(["attachment"]))
    with patch.object(storage, "delete") as delete, patch.object(Record, "save", autospec=True) as save:
        assert not trees.all_valid()
        assert "file invariant" in str(form.non_field_errors())
        save.assert_not_called()
        delete.assert_not_called()
    row.refresh_from_db()
    assert row.attachment.name == stored
    assert storage.exists(stored)


@pytest.mark.parametrize("active", [False, True])
def test_dynamic_model_form_refuses_configuration_before_any_save(row, active):
    class Dynamic(record_form([])):
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["dynamic"])]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["dynamic"] = forms.JSONField()

    assert "dynamic" not in Dynamic.base_fields
    form = Dynamic(instance=row, data={"active": "on", "dynamic": '{"ok": 1}'} if active else {})
    with patch.object(Record, "save", autospec=True) as save:
        with pytest.raises(ImproperlyConfigured, match=r"active.*dynamic"):
            form.save()
        save.assert_not_called()


@pytest.mark.parametrize("empty", [False, None, "", []])
def test_explicit_values_reach_custom_persistence_hook_unmodified(row, monkeypatch, empty):
    field = Record._meta.get_field("blank_text")
    original = field.save_form_data
    received = []

    def save_form_data(instance, value):
        received.append(value)
        original(instance, f"native:{value!r}")

    monkeypatch.setattr(field, "save_form_data", save_form_data)
    with patch.object(Record, "save", autospec=True) as save:
        with pytest.raises(ImproperlyConfigured, match=r"active.*blank_text"):
            record_form(["blank_text"])(instance=row, data={}).is_valid()
        save.assert_not_called()
    assert received == []
    form = record_form(["blank_text"], empty_values={"blank_text": empty})(instance=row, data={})
    assert form.is_valid(), form.errors
    assert received and all(value is empty for value in received)
    form.save()
    row.refresh_from_db()
    assert row.blank_text == f"native:{empty!r}"


@pytest.mark.parametrize("name", ["number", "parent"])
def test_nonnull_numeric_and_foreign_key_refuse_automatic_clear_before_save(row, monkeypatch, name):
    monkeypatch.setattr(Record._meta.get_field(name), "null", False)
    form = record_form([name])(instance=row, data={})
    with patch.object(Record, "save", autospec=True) as save:
        with pytest.raises(ImproperlyConfigured, match=rf"active.*{name}"):
            form.save()
        save.assert_not_called()


@isolate_apps()
@pytest.mark.parametrize("kind", ["json", "custom"])
def test_json_and_custom_model_fields_need_explicit_native_clearing(kind):
    class CustomText(models.CharField):
        pass

    class Unsupported(models.Model):
        active = models.BooleanField(default=False)
        value = models.JSONField(null=True, blank=True) if kind == "json" else CustomText(max_length=30, blank=True)

        class Meta:
            app_label = "conditional_probe"

    class CustomForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["value"])]

        class Meta:
            model = Unsupported
            fields = ["active", "value"]

    with patch.object(Unsupported, "save", autospec=True) as save:
        with pytest.raises(ImproperlyConfigured, match=r"active.*value"):
            CustomForm(data={}).save()
        save.assert_not_called()
    empty = [] if kind == "json" else ""
    CustomForm.cv_conditional_groups[0].empty_values["value"] = empty
    form = CustomForm(data={})
    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    assert instance.value is empty


def test_suppressed_field_error_does_not_suppress_inherited_nonfield_invariant(row):
    class Invariant(forms.ModelForm):
        class Meta:
            model = Record
            fields = ["active", "blank_text"]

        def clean(self):
            cleaned = super().clean()
            assert "blank_text" in self.errors
            self.add_error(None, "application invariant")
            return cleaned

    class Conditional(ConditionalGroupFormMixin, Invariant):
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("active"), ["blank_text"])]

    form = Conditional(instance=row, data={"blank_text": "x" * 200})
    with patch.object(Record, "save", autospec=True) as save:
        assert not form.is_valid()
        assert "blank_text" not in form.errors
        assert form.non_field_errors() == ["application invariant"]
        with pytest.raises(ValueError):
            form.save()
        save.assert_not_called()
    row.refresh_from_db()
    assert row.blank_text == "default text"
