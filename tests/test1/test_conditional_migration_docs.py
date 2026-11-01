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
from django.forms.models import inlineformset_factory
from django.template import Context, Engine
from django.test import RequestFactory
from lxml import html

from crud_views.lib.conditional import ToggleGroup
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
        parent = Author.objects.create(pk="12345678-1234-1234-1234-123456789abc", name="projection")
        child, fields, grammar, offset = UUIDFragmentRow, ["text"], FormSet.PK.UUID, 2
    klass = inlineformset_factory(type(parent), child, formset=InlineFormSet, fields=fields, extra=1)
    tree = FormSets(formsets={"rows": FormSet(title="Rows", klass=klass, pk=grammar, fields=fields, path="/editor/")})
    main = forms.modelform_factory(type(parent), fields=[])(instance=parent)
    tree.init(RequestFactory().get("/editor/"), main)
    formset = tree.x_formsets[0]
    assert json.loads(formset.json_data) == projections[offset]
    assert json.loads(formset.forms[0].json_data) == projections[offset + 1]
    assert projections[offset]["pk"] == grammar.value
    assert projections[offset + 1]["pk"] == str(grammar)
    assert projections[offset]["pk"] != str(parent.pk)


def test_reference_evidence_and_example_comments_remain_explicit():
    text = CONDITIONAL.read_text()
    assert "ImageField" in text and "reference-only" in text
    assert "Pillow" in text and "image-byte decoding" in text
    assert "multipart FileField" in text
    example = (ROOT / "examples/bootstrap5/conditional/models.py").read_text()
    assert "crud_views.W320" not in example
    assert "crud_views.E312" in example
    assert "docs/reference/conditional.md#clearing-matrix" in example
