import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.utils import translation
from lxml import html

import crud_views
from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
from tests.lib.helper.user import user_viewset_permission

SRC = Path(crud_views.__file__).resolve().parent.parent
TOKEN = re.compile(r"(?<![\w-])btn(?:-[\w-]+)?(?![\w-])")
LITERAL = re.compile(r"""\{%\s*cv_button_class\s+(["'])([^"']+)\1\s+(["'])([^"']+)\3""")
EXEMPT_TOKENS = {"btn-close"}
EXEMPT_FILES = {"crud_views/lib/button_classes.py"}


def _shipped_files():
    for pattern in ("*/templates/**/*.html", "*/static/**/*.js", "**/*.py"):
        for path in SRC.glob(pattern):
            if "/vendor/" in path.as_posix():
                continue
            yield path


def test_no_button_class_literal_in_shipped_templates_python_or_js():
    offenders = set()
    scanned = {"html": 0, "js": 0, "py": 0}
    for path in _shipped_files():
        rel = path.relative_to(SRC).as_posix()
        scanned[path.suffix.lstrip(".")] += 1
        if rel in EXEMPT_FILES:
            continue
        for token in TOKEN.findall(path.read_text()):
            if token not in EXEMPT_TOKENS:
                offenders.add((rel, token))
    assert all(scanned.values()), scanned
    assert sorted(offenders) == []


def test_every_literal_slot_in_templates_is_a_default_key():
    pairs = []
    for path in SRC.glob("*/templates/**/*.html"):
        for m in LITERAL.finditer(path.read_text()):
            pairs.append(f"{m.group(2)}:{m.group(4)}")
    assert len(pairs) >= 15, pairs
    assert sorted(set(pairs) - set(DEFAULT_BUTTON_CLASSES)) == []


def _render_formset_controls():
    tpl = Template('{% include "crud_views/formsets/control.html" %}')
    rendered = tpl.render(
        Context({"formset": SimpleNamespace(can_order=True, can_delete=True), "form": SimpleNamespace(prefix="p-0")})
    )
    return html.fromstring(rendered)


def test_formset_controls_from_table():
    doc = _render_formset_controls()
    assert [g.get("class") for g in doc.cssselect("fieldset")] == ["btn-group"] * 3
    buttons = doc.cssselect("button")
    assert len(buttons) == 4
    assert all(b.get("class").startswith("btn btn-light cv-form-ctrl-") for b in buttons)
    delete = doc.cssselect("button.cv-form-ctrl-delete")[0]
    assert delete.get("data-cv-class") == "btn btn-light"
    assert delete.get("data-cv-class-danger") == "btn btn-danger"

    with override_settings(
        CRUD_VIEWS_BUTTON_CLASSES={"formset:control": "x-ctrl", "formset:control-danger": "x-danger"}
    ):
        delete = _render_formset_controls().cssselect("button.cv-form-ctrl-delete")[0]
    assert delete.get("data-cv-class") == "x-ctrl"
    assert delete.get("data-cv-class-danger") == "x-danger"


@pytest.mark.django_db
def test_card_order_and_language_from_table(client):
    from tests.test1.app.views import cv_publisher_order

    user = User.objects.create_user(username="user_btn_order", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client.force_login(user)
    response = client.get("/publisher_order/card/?order=name&dir=desc")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    asc = doc.cssselect('button[name="dir"][value="asc"]')[0]
    desc = doc.cssselect('button[name="dir"][value="desc"]')[0]
    assert asc.get("class") == "btn btn-outline-secondary"
    assert desc.get("class") == "btn btn-outline-secondary active"
    assert doc.cssselect("#cv-card-order-form fieldset")[0].get("class") == "btn-group btn-group-sm"

    request = RequestFactory().get("/some/path/")
    with translation.override("en"):
        rendered = Template("{% load crud_views %}{% cv_language_selector %}").render(Context({"request": request}))
    toggle = html.fromstring(rendered).cssselect("button.dropdown-toggle")[0]
    assert toggle.get("class") == "btn btn-outline-secondary dropdown-toggle"
