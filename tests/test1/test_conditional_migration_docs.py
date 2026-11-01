"""Execute the conditional migration recipes and compare published wire projections."""

import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.utils import render_crispy_form
from django import forms
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.template import Context, Engine
from django.test import RequestFactory
from lxml import html

from crud_views.lib.conditional import ToggleGroup
from crud_views.lib.crispy import CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from tests.test1.app.models import Author, Book, Profile, Publisher, UUIDFragmentRow
from tests.test1.app.models import ConditionalPersistenceRecord as Record

ROOT = Path(__file__).resolve().parents[2]
CONDITIONAL = ROOT / "docs/reference/conditional.md"
FORMSETS = ROOT / "docs/reference/formsets.md"
pytestmark = pytest.mark.django_db


def recipe(path, heading, language, count=1):
    text = path.read_text()
    assert text.count(heading) == 1, f"Missing or duplicated published section: {heading}"
    section = text.split(heading, 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
    fences = re.findall(rf"^```{language}\n(.*?)^```", section, re.MULTILINE | re.DOTALL)
    assert len(fences) == count, f"Expected {count} complete {language} recipes in {heading}"
    return fences


@pytest.mark.parametrize("prefix", [None, "editor-0", 'editor"<&-0'])
def test_published_wrapper_uses_real_bound_context_and_escaping(prefix):
    template = recipe(CONDITIONAL, "### Copied conditional wrapper", "django")[0]

    class ContactForm(forms.Form):
        active = forms.BooleanField(required=False)
        note = forms.CharField(required=False)

    form = ContactForm(prefix=prefix)
    helper = FormHelper()
    helper.layout = Layout("active", ToggleGroup("active", "note", legend="Contact"))
    render = Engine.get_default().from_string(template)
    with patch(
        "crud_views.lib.conditional.layout.render_to_string", side_effect=lambda _, ctx: render.render(Context(ctx))
    ):
        tree = html.fromstring(render_crispy_form(form, helper))
    checkbox = tree.xpath('.//input[@type="checkbox"]')[0]
    group = tree.xpath(".//*[@cv-data-toggle-group]")[0]
    assert group.get("cv-data-toggle-field") == checkbox.get("name") == form.add_prefix("active")
    assert group.tag == "fieldset"
    assert group.xpath("./legend")[0].text == "Contact"
    assert group.xpath(".//input[@name=$name]", name=form.add_prefix("note"))


@pytest.mark.parametrize("field_name", ["attachment", "image"])
@pytest.mark.parametrize("empty_value", [False, "", None])
def test_published_explicit_file_values_persist_native_reference_semantics(
    tmp_path, monkeypatch, field_name, empty_value
):
    source = recipe(CONDITIONAL, "### Explicit file reference recipe", "python")[0]
    namespace = {}
    exec(compile(source, str(CONDITIONAL), "exec"), namespace)
    form_class = namespace["reference_form"](Record, field_name=field_name, empty_value=empty_value)
    storage = FileSystemStorage(location=tmp_path)
    monkeypatch.setattr(Record._meta.get_field(field_name), "storage", storage)
    stored = storage.save("existing.bin", ContentFile(b"existing reference bytes"))
    row = Record.objects.create(parent=Profile.objects.create(name="parent"), **{field_name: stored})
    # No uploaded bytes: even the ImageField case tests references only.
    form = form_class(instance=row, data={})
    with patch.object(storage, "delete", wraps=storage.delete) as delete, patch.object(storage, "save") as write:
        assert form.is_valid(), form.errors
        form.save()
        delete.assert_not_called()
        write.assert_not_called()
    row.refresh_from_db()
    assert getattr(row, field_name).name == (stored if empty_value is None else "")
    with storage.open(stored, "rb") as content:
        assert content.read() == b"existing reference bytes"


@pytest.mark.parametrize("kind", ["integer", "uuid"])
def test_published_formset_and_row_json_match_actual_projection(kind):
    projections = [json.loads(value) for value in recipe(FORMSETS, "### Exact JSON projections", "json", count=4)]
    if kind == "integer":
        parent = Publisher.objects.create(pk=42, name="projection")
        child, fields, grammar, offset = Book, ["title"], FormSet.PK.INT, 0
    else:
        parent = Author.objects.create(pk="12345678-1234-1234-1234-123456789abc", first_name="projection")
        child, fields, grammar, offset = UUIDFragmentRow, ["text"], FormSet.PK.UUID, 2
    klass = inlineformset_factory(
        type(parent), child, formset=InlineFormSet, form=CrispyModelForm, fields=fields, extra=1
    )
    tree = FormSets(formsets={"rows": FormSet(title="Rows", klass=klass, pk=grammar, fields=fields, path="/editor/")})
    main = forms.modelform_factory(type(parent), fields=[])(instance=parent)
    tree.init(RequestFactory().get("/editor/"), main)
    formset = tree.x_formsets[0]
    assert json.loads(formset.json_data) == projections[offset]
    assert json.loads(formset.forms[0].json_data) == projections[offset + 1]
    assert projections[offset]["pk"] == grammar.value
    assert projections[offset + 1]["pk"] == str(grammar)
    assert projections[offset]["pk"] != str(parent.pk)


def test_published_native_controls_follow_actual_delete_field_presence():
    source = recipe(FORMSETS, "### Native row capability recipe", "django")[0]
    parent = Publisher.objects.create(name="controls")
    Book.objects.create(publisher=parent, title="initial")
    klass = inlineformset_factory(
        Publisher, Book, fields=["title"], extra=1, can_delete=True, can_delete_extra=False, can_order=True
    )
    native = klass(instance=parent, prefix="rows")
    render = Engine.get_default().from_string(source)
    for index, form in enumerate(native.forms):
        tree = html.fromstring(render.render(Context({"form": form, "formset": native})))
        controls = tree.xpath(".//button")
        classes = {button.get("class") for button in controls}
        assert {"cv-form-ctrl-add", "cv-form-ctrl-up", "cv-form-ctrl-down"} <= classes
        assert ("cv-form-ctrl-delete" in classes) is (index == 0)
        assert ("DELETE" in form.fields) is (index == 0)
        assert all(button.get("type") == "button" for button in controls)
        assert all(button.get("cv-data-formset-form-prefix") == form.prefix for button in controls)
        assert all(button.get("aria-label") for button in controls)


@pytest.mark.parametrize("adapter", [InlineFormSet, BaseInlineFormSet], ids=["package", "native"])
@pytest.mark.parametrize("violation", ["extra", "identity"])
def test_published_reclean_sequence_reapplies_policy(adapter, violation):
    # Native accepted adapters supply rendering context without inheriting package clean().
    from tests.test1.test_formsets_policy import PolicyNativeInlineFormSet

    if adapter is BaseInlineFormSet:
        adapter = PolicyNativeInlineFormSet
    parent = Publisher.objects.create(name="reclean")
    child = Book.objects.create(publisher=parent, title="existing")
    klass = inlineformset_factory(
        Publisher, Book, formset=adapter, form=CrispyModelForm, fields=["title"], extra=1, edit_only=True
    )
    prefix = f"rows-{parent.pk}-0"
    data = {
        f"{prefix}-TOTAL_FORMS": "2",
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": str(child.pk) if violation == "extra" else "999999",
        f"{prefix}-0-title": "existing",
        f"{prefix}-1-title": "forged" if violation == "extra" else "",
    }
    formsets = FormSets(formsets={"rows": FormSet(title="Rows", klass=klass, fields=["title"])})
    main = forms.modelform_factory(Publisher, fields=[])(instance=parent, data=data)
    formsets.init(RequestFactory().post("/editor/", data), main)
    namespace = {
        "formsets": formsets,
        "expected_code": "cv_additions_not_allowed" if violation == "extra" else "cv_invalid_row",
    }
    source = recipe(FORMSETS, "### Repeated validation regression recipe", "python")[0]
    with patch.object(FormSets, "save") as save, patch.object(klass, "save") as child_save:
        exec(compile(source, str(FORMSETS), "exec"), namespace)
        save.assert_not_called()
        child_save.assert_not_called()
    child.refresh_from_db()
    assert child.title == "existing"
    assert Book.objects.filter(publisher=parent).count() == 1


def test_reference_evidence_and_example_comments_remain_explicit():
    text = CONDITIONAL.read_text()
    assert "ImageField" in text and "reference-only" in text
    assert "Pillow" in text and "image-byte decoding" in text
    assert "multipart FileField" in text
    example = (ROOT / "examples/bootstrap5/conditional/models.py").read_text()
    assert "crud_views.W320" not in example
    assert "crud_views.E312" in example
    assert "docs/reference/conditional.md#clearing-matrix" in example


def test_breaking_changes_pair_migration_recipes_and_public_inventory():
    changelog = (ROOT / "CHANGELOG.md").read_text().split("### Breaking", 1)[1].split("\n### ", 1)[0]
    migration = (ROOT / "docs/migrating-1.0.md").read_text()
    assert "the wrong index. That is a known limitation" not in migration
    changes = {
        "Conditional bound markers and lifecycle": "conditional-bound-markers-and-lifecycle",
        "Conditional clearing and E312": "conditional-clearing-and-e312",
        "Formset row validation before saving": "formset-row-validation-before-saving",
    }
    for title, anchor in changes.items():
        assert f"**{title}.**" in changelog, f"Missing paired Breaking item: {title}"
        assert f"docs/migrating-1.0.md#{anchor}" in changelog
        assert migration.count(f"### {title}\n") == 1
        section = migration.split(f"### {title}\n", 1)[1].split("\n### ", 1)[0]
        assert "reference/" in section and "recipe" in section
    inventory = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-PUBLIC-SURFACE.md"
    assert inventory.is_file(), "Phase 7 needs an explicit supported-surface handoff"
    text = inventory.read_text()
    for name in (
        "cv.initConditional(root=document)",
        "cv.initFormsets(root=document)",
        "cv_toggle_field",
        "cv:formset:row-added",
        "{prefix, rows}",
        "{html, rows}",
        "E312",
        "E310",
        "E311",
        "W321",
        "XFormSet",
        "A8",
        "jQuery",
    ):
        assert name in text
    assert "test_conditional_migration_docs.py" in text
    assert "not complete" in text
