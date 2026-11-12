# tests/test1/test_conditional_layout.py
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row
from crispy_forms.utils import render_crispy_form
from django import forms
from django.test import override_settings
from django.utils.html import escape
from lxml import html as lxml_html

from crud_views.lib import button_classes as bc
from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.layout import ToggleGroup
from crud_views.lib.conditional.toggle import ModelFieldToggle
from crud_views.lib.crispy import Column6
from tests.test1.app.models import Profile

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _isolate_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    bc.reset_button_classes_cache()


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
    assert "cv-data-toggle-group" in html
    assert "email" in html
    assert "phone" in html


def test_toggle_group_does_not_inline_scripts():
    # toggle.js is registered globally via crud_views_settings.javascript() and
    # rendered by the cv_js tag — the layout element itself must stay script-free.
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "toggle.js" not in html
    assert "<script" not in html


def test_toggle_js_registered_in_settings_javascript():
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.javascript()["toggle"] == "crud_views/js/toggle.js"


class _LegendLayoutForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        h = FormHelper()
        h.layout = Layout(
            Row(Column6("name")),
            Row(Column6("with_contact")),
            ToggleGroup(
                "with_contact",
                Row(Column6("email"), Column6("phone")),
                legend="Contact details",
            ),
        )
        return h


def test_toggle_group_legend_renders_fieldset():
    form = _LegendLayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "<fieldset" in html
    legend = lxml_html.fromstring(html).cssselect("fieldset.cv-toggle-group")[0].xpath("./legend")[0]
    assert legend.text_content() == "Contact details"
    assert legend.get("class") == ""
    # marker lives on the fieldset so toggle.js hides the whole group
    assert 'cv-data-toggle-field="with_contact"' in html
    assert "cv-data-toggle-group" in html


@pytest.mark.parametrize(
    "project,expected",
    [
        ({}, "theme-conditional"),
        ({"conditional:legend": "project-conditional"}, "project-conditional"),
        ({"conditional:legend": ""}, ""),
        ({"formset:legend": "project-formset"}, "theme-conditional"),
        ({"formset:legend": ""}, "theme-conditional"),
    ],
)
def test_toggle_group_legend_classes_follow_independent_layers(project, expected):
    bc.register_button_classes({"conditional:legend": "theme-conditional", "formset:legend": "theme-formset"})
    form = _LegendLayoutForm(prefix="editor-0")
    helper = form.helper
    helper.layout.fields[-1].css_class = "caller-group"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=project):
        doc = lxml_html.fromstring(render_crispy_form(form, helper=helper))
    group = doc.cssselect("fieldset.cv-toggle-group")[0]
    assert set(group.get("class").split()) == {"cv-toggle-group", "caller-group"}
    assert "cv-data-toggle-group" in group.attrib
    assert group.get("cv-data-toggle-field") == "editor-0-with_contact"
    legend = group.xpath("./legend")[0]
    assert legend.get("class") == expected
    assert legend.text_content() == "Contact details"


def test_toggle_group_legend_escapes_plain_text_and_classes():
    title = '<script data-legend="injected">Contact & details</script>'
    classes = '" data-injected="yes"><img src=x> & legend'
    bc.register_button_classes({"conditional:legend": classes})
    form = _LegendLayoutForm(prefix="editor-0")
    helper = form.helper
    helper.layout.fields[-1].legend = title
    rendered = render_crispy_form(form, helper=helper)
    assert str(escape(title)) in rendered
    assert f'class="{escape(classes)}"' in rendered
    doc = lxml_html.fromstring(rendered)
    legend = doc.cssselect("fieldset.cv-toggle-group")[0].xpath("./legend")[0]
    assert legend.text_content() == title
    assert legend.attrib == {"class": classes}
    assert len(legend) == 0
    assert not doc.cssselect("script, img, [data-injected], [data-legend]")


def test_toggle_group_without_legend_stays_a_div():
    # backward compat: no legend => current <div> rendering, no fieldset
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "<fieldset" not in html
    assert "<legend" not in html
    assert "cv-data-toggle-group" in html


@pytest.mark.parametrize("prefix", ["account", "rows-0", 'account<&"'])
def test_toggle_group_emits_escaped_exact_bound_name(prefix):
    from django.utils.html import escape

    form = _LayoutForm(prefix=prefix)
    html = render_crispy_form(form, helper=form.helper)
    assert f'cv-data-toggle-field="{escape(form.add_prefix("with_contact"))}"' in html


def _resolve_tracer_node(root):
    """Resolve and probe only when the explicitly enabled tracer calls us."""
    selected = os.environ.get("CV_FOCUS_NODE")
    if selected is None:
        manifest = root / ".planning/phases/06-form-button-leaf/06-JS-RUNTIME.json"
        try:
            selected = json.loads(manifest.read_text())["node"]["path"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            pytest.fail(f"Conditional tracer cannot read Node manifest {manifest}: {exc}; set CV_FOCUS_NODE")
    if not isinstance(selected, str) or not selected:
        pytest.fail(f"Conditional tracer invalid Node path {selected!r}; set CV_FOCUS_NODE to an executable")
    executable = shutil.which(selected)
    if executable is None:
        pytest.fail(f"Conditional tracer Node {selected!r} unavailable; set CV_FOCUS_NODE to an executable")
    try:
        version = subprocess.run(
            [executable, "--version"], cwd=root, capture_output=True, text=True, check=True, timeout=15
        ).stdout.strip()
        jsdom = subprocess.run(
            [executable, "-e", 'require("jsdom"); console.log(require("jsdom/package.json").version)'],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.fail(
            f"Conditional tracer Node {selected!r} or repository jsdom unusable: {exc}; check runtime/dependencies"
        )
    return executable, version, jsdom


def test_tracer_disabled_import_never_probes_runtime(monkeypatch):
    import inspect

    monkeypatch.delenv("CV_CONDITIONAL_TRACER", raising=False)
    monkeypatch.delenv("CV_FOCUS_NODE", raising=False)
    monkeypatch.setenv("PATH", "")

    def forbidden(*args, **kwargs):
        pytest.fail("Disabled tracer performed a runtime probe or manifest read")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(shutil, "which", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    spec = importlib.util.spec_from_file_location("_conditional_layout_disabled", __file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.test_tracer_rendered_conditional_round_trip.__test__ is False
    ordinary = [
        (name, obj)
        for name, obj in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("test_") and getattr(obj, "__test__", True)
    ]
    assert any(name == "test_toggle_group_renders_marker_attributes" for name, _ in ordinary)


def test_tracer_rendered_conditional_round_trip(monkeypatch, tmp_path, record_property):
    root = Path(__file__).resolve().parents[2]
    node, version, jsdom = _resolve_tracer_node(root)
    with monkeypatch.context() as patch:
        patch.delenv("CV_FOCUS_NODE", raising=False)
        default_node, _, _ = _resolve_tracer_node(root)
        manifest = root / ".planning/phases/06-form-button-leaf/06-JS-RUNTIME.json"
        assert default_node == json.loads(manifest.read_text())["node"]["path"]
    record_property("tracer_node_path", node)
    record_property("tracer_node_version", version)
    record_property("tracer_jsdom_version", jsdom)
    with monkeypatch.context() as patch:
        patch.setenv("CV_FOCUS_NODE", node)
        assert _resolve_tracer_node(root) == (node, version, jsdom)
    for override in ["", str(tmp_path / "missing-node")]:
        with monkeypatch.context() as patch:
            patch.setenv("CV_FOCUS_NODE", override)
            with pytest.raises(pytest.fail.Exception, match=r"Conditional tracer.*Node"):
                _resolve_tracer_node(root)
    with monkeypatch.context() as patch:
        patch.delenv("CV_FOCUS_NODE", raising=False)
        with pytest.raises(pytest.fail.Exception, match="manifest"):
            _resolve_tracer_node(tmp_path)
        patch.setattr(Path, "read_text", lambda *a, **kw: "{invalid")
        with pytest.raises(pytest.fail.Exception, match="manifest"):
            _resolve_tracer_node(root)
    with monkeypatch.context() as patch:
        patch.delenv("CV_FOCUS_NODE", raising=False)
        patch.setattr(Path, "read_text", lambda *a, **kw: json.dumps({"node": {"path": str(tmp_path / "absent")}}))
        with pytest.raises(pytest.fail.Exception, match="unavailable"):
            _resolve_tracer_node(root)
    with monkeypatch.context() as patch:
        patch.setenv("CV_FOCUS_NODE", node)

        def unusable(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr="unusable runtime/jsdom")

        patch.setattr(subprocess, "run", unusable)
        with pytest.raises(pytest.fail.Exception, match="unusable"):
            _resolve_tracer_node(root)

    class ContactForm(ConditionalGroupFormMixin, _LayoutForm):
        cv_conditional_groups = [
            ConditionalGroup(ModelFieldToggle("with_contact"), ["email", "phone"], required=["email"])
        ]

    first = Profile.objects.create(name="first", with_contact=True, email="first@example.com", phone="111")
    second = Profile.objects.create(name="second", with_contact=True, email="second@example.com", phone="222")
    rendered = []
    for index, row in enumerate([first, second]):
        form = ContactForm(instance=row, prefix=f"rows-{index}")
        helper = form.helper
        helper.form_tag = False
        rendered.append(render_crispy_form(form, helper=helper))
    html = "<form>" + "".join(rendered) + "</form>"
    script = r"""
const fs = require("node:fs"), assert = require("node:assert/strict");
const {JSDOM} = require("jsdom");
const dom = new JSDOM(fs.readFileSync(0, "utf8"), {runScripts: "outside-only"});
const w = dom.window, d = w.document;
w.eval(fs.readFileSync("src/crud_views/static/crud_views/js/toggle.js", "utf8"));
d.dispatchEvent(new w.Event("DOMContentLoaded"));
const groups = [...d.querySelectorAll("[cv-data-toggle-group]")];
assert.equal(groups.length, 2);
const target = d.getElementsByName("rows-1-with_contact")[0];
target.click();
assert.equal(groups[0].style.display, "");
assert.equal(groups[1].style.display, "none");
assert.equal(d.getElementsByName("rows-0-email")[0].disabled, false);
assert.equal(d.getElementsByName("rows-1-email")[0].disabled, true);
const payload = Object.fromEntries(new w.FormData(target.form));
assert.equal(payload["rows-1-name"], "second");
assert.equal("rows-1-email" in payload, false);
console.log(JSON.stringify(payload));
dom.window.close();
"""
    result = subprocess.run([node, "-e", script], input=html, cwd=root, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"Node tracer {node} failed: {result.stderr}"
    form = ContactForm(data=json.loads(result.stdout), instance=second, prefix="rows-1")
    assert form.is_valid(), form.errors
    form.save()
    first.refresh_from_db()
    second.refresh_from_db()
    assert (first.with_contact, first.email, first.phone) == (True, "first@example.com", "111")
    assert (second.with_contact, second.email, second.phone) == (False, None, None)


test_tracer_rendered_conditional_round_trip.__test__ = os.environ.get("CV_CONDITIONAL_TRACER") == "1"


@pytest.mark.parametrize("legend", [None, "Choice <details>"])
@pytest.mark.parametrize("prefix", ["rows-0", 'rows [] <&"'])
def test_value_toggle_render_metadata(legend, prefix):
    from crud_views.lib.conditional.toggle import ValueToggle

    tokens = ['value" <script> & []', " spaced ", "0"]
    descriptor = ValueToggle("kind", values=tokens)

    class ChoiceForm(forms.Form):
        kind = forms.ChoiceField(choices=[(token, token) for token in tokens])
        detail = forms.CharField(required=False)
        active = forms.BooleanField(required=False)
        legacy_detail = forms.CharField(required=False)

    form = ChoiceForm(prefix=prefix)
    helper = FormHelper()
    assert ToggleGroup(toggle_field=descriptor).toggle_field is descriptor
    helper.layout = Layout(
        "kind", ToggleGroup(descriptor, "detail", legend=legend), "active", ToggleGroup("active", "legacy_detail")
    )
    bc.register_button_classes({"conditional:legend": "choice-legend", "formset:legend": "other-legend"})
    rendered = render_crispy_form(form, helper=helper)
    doc = lxml_html.fromstring(rendered)
    group, legacy = doc.cssselect("[cv-data-toggle-group]")
    assert json.loads(group.get("cv-data-toggle-values")) == tokens
    assert group.get("cv-data-toggle-field") == form.add_prefix("kind")
    assert group.tag == ("fieldset" if legend else "div")
    if legend:
        title = group.xpath("./legend")[0]
        assert title.text_content() == legend and title.get("class") == "choice-legend"
    assert "cv-data-toggle-values" not in legacy.attrib
    assert legacy.get("cv-data-toggle-field") == form.add_prefix("active")
    assert not doc.cssselect("script")
