"""#239: the four form content templates extend one frame, and the delete protection alert is its own snippet.

Golden files were captured from main before the templates moved into the frame. Regenerate ONLY when a change to the
stock markup is intended: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_form_frame.py
"""

import os
import re
from pathlib import Path

import pytest
from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings

GOLDEN_DIR = Path(__file__).parent / "golden" / "form_frame"

FORM_TEMPLATES = {
    "create": "crud_views/view_create.content.html",
    "update": "crud_views/view_update.content.html",
    "custom_form": "crud_views/view_custom_form.content.html",
    "delete": "crud_views/view_delete.content.html",
}

PROTECTION_ERRORS = ["Publisher has 2 books.", "Publisher is referenced by a contract."]

THEME_FRAME = (
    '{% block cv_form_frame %}{% if request.headers.x_cv_modal != "true" %}<div class="theme-card">{% endif %}'
    '{% block cv_form_body %}{% endblock %}{% if request.headers.x_cv_modal != "true" %}</div>{% endif %}{% endblock %}'
)


class NameForm(forms.Form):
    name = forms.CharField()


def _render(template, headers=None, **extra):
    request = RequestFactory().get("/", headers=headers or {})
    context = {"form": NameForm(), "request": request, "view": None, **extra}
    return render_to_string(template, context, request=request)


def _norm(markup: str) -> str:
    markup = re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]*"', r'\1CSRF"', markup)
    markup = re.sub(r">\s+<", "><", markup)
    return re.sub(r"\s+", " ", markup).strip()


def _check_golden(name: str, markup: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_norm(markup) + "\n")
    assert _norm(markup) == path.read_text().strip()


def _theme_templates(overrides: dict):
    """The test engine with a locmem loader in front, the way a theme app listed first shadows crud_views."""
    engine = dict(settings.TEMPLATES[0])
    options = dict(engine["OPTIONS"])
    options["loaders"] = [
        ("django.template.loaders.locmem.Loader", overrides),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    engine.update(APP_DIRS=False, OPTIONS=options)
    return override_settings(TEMPLATES=[engine])


@pytest.mark.parametrize("name", list(FORM_TEMPLATES))
def test_stock_markup_unchanged(name):
    from tests.test1.test_theme_form_ownership import assert_owned_form_markup

    markup = _render(FORM_TEMPLATES[name])
    assert_owned_form_markup(markup)
    _check_golden(name, markup)


def test_stock_delete_protection_markup_unchanged():
    html = _render(FORM_TEMPLATES["delete"], delete_protection_errors=PROTECTION_ERRORS)
    _check_golden("delete_protection", html)


@pytest.mark.parametrize("name", list(FORM_TEMPLATES))
def test_theme_frame_wraps_the_form(name):
    from tests.test1.test_theme_form_ownership import assert_owned_form_markup

    with _theme_templates({"crud_views/snippets/form_frame.html": THEME_FRAME}):
        html = _norm(_render(FORM_TEMPLATES[name]))
    assert html.startswith('<div class="theme-card"><form class="cv-form"')
    assert html.endswith("</form></div>")
    assert html.count("<form") == html.count("</form>")
    assert_owned_form_markup(html)


@pytest.mark.parametrize("name", list(FORM_TEMPLATES))
def test_theme_frame_leaves_the_modal_bare(name):
    from tests.test1.test_theme_form_ownership import assert_owned_form_markup

    with _theme_templates({"crud_views/snippets/form_frame.html": THEME_FRAME}):
        html = _norm(_render(FORM_TEMPLATES[name], headers={"X-CV-Modal": "true"}))
    assert "theme-card" not in html
    assert html.startswith('<form class="cv-form"')
    assert_owned_form_markup(html)


def test_theme_frame_wraps_the_protection_alert():
    with _theme_templates({"crud_views/snippets/form_frame.html": THEME_FRAME}):
        html = _norm(_render(FORM_TEMPLATES["delete"], delete_protection_errors=PROTECTION_ERRORS))
    assert html.startswith('<div class="theme-card"><div class="alert alert-danger" role="alert">')


def test_protection_alert_overridable_on_its_own():
    snippet = '<div class="theme-alert">{% for error in delete_protection_errors %}<p>{{ error }}</p>{% endfor %}</div>'
    with _theme_templates({"crud_views/snippets/delete/protection_errors.html": snippet}):
        html = _norm(_render(FORM_TEMPLATES["delete"], delete_protection_errors=PROTECTION_ERRORS))
    assert html == (
        '<div class="theme-alert"><p>Publisher has 2 books.</p><p>Publisher is referenced by a contract.</p></div>'
    )


@pytest.mark.parametrize("choices", [False, True])
@pytest.mark.parametrize("themed", [False, True])
def test_workflow_action_frame(choices, themed):
    from lxml import html

    from tests.test1.test_theme_form_ownership import _RawForms

    overrides = {"crud_views/snippets/form_frame.html": THEME_FRAME} if themed else {}
    with _theme_templates(overrides):
        markup = _render("crud_views_workflow/view_workflow.action.html", has_workflow_choices=choices)
    scanner = _RawForms()
    scanner.feed(markup)
    assert not scanner.stack
    root = html.fragment_fromstring(markup, create_parent="div")
    cards = root.cssselect(".theme-card")
    assert len(cards) == int(themed)
    body = cards[0] if themed else root
    if choices:
        assert len(scanner.forms) == 1
        assert len(scanner.forms[0]["tokens"]) == 1
        heading, form = list(body)
        assert heading.text_content() == "Workflow Action"
        assert form.tag == "form"
        assert form.get("class") == "cv-form"
        assert form.get("method") == "post"
        assert "novalidate" in form.attrib
        assert "action" not in form.attrib and "enctype" not in form.attrib
    else:
        assert scanner.forms == []
        assert not body.cssselect("h5, form, input, button")
        assert body.text_content().strip() == "There are no workflow steps available from the current state."
