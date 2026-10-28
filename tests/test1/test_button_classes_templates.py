import re
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import translation
from lxml import html

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES, FORM_KINDS, VARIANT_LOCATIONS
from crud_views.lib.view.button_data import LOCATIONS, cv_button_data
from crud_views.lib.view.label_mode import LABEL_MODES
from tests.lib.helper.user import user_viewset_permission

SRC = Path(__file__).resolve().parents[2] / "src"
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
    assert len(pairs) >= 20, pairs
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
    assert [(b.get("title"), b.get("data-cv-tooltip")) for b in buttons] == [
        ("Move up", "formset"),
        ("Move down", "formset"),
        ("Add row", "formset"),
        ("Delete row", "formset"),
    ]
    assert all(b.get("title") == b.get("aria-label") for b in buttons)

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
    assert asc.get("data-cv-tooltip") == "card-order"
    assert desc.get("data-cv-tooltip") == "card-order"
    assert asc.get("title") == "Ascending"
    # the accessible name must not depend on title: a non-Bootstrap adapter removes it (see javascript.md)
    assert asc.get("aria-label") == "Ascending"
    assert desc.get("aria-label") == "Descending"
    assert doc.cssselect("#cv-card-order-form fieldset")[0].get("class") == "btn-group btn-group-sm"

    request = RequestFactory().get("/some/path/")
    with translation.override("en"):
        rendered = Template("{% load crud_views %}{% cv_language_selector %}").render(Context({"request": request}))
    toggle = html.fromstring(rendered).cssselect("button.dropdown-toggle")[0]
    assert toggle.get("class") == "btn btn-outline-secondary dropdown-toggle"


# --- the rendering guard (#227): every class in the button chain comes from the table or the cv- namespace -------

SENTINEL_CLASSES = {key: "x-" + key.replace(":", "-") for key in DEFAULT_BUTTON_CLASSES}
SENTINELS = frozenset(SENTINEL_CLASSES.values())
# Bootstrap tokens the chain still carries because they are behaviour hooks, not looks. #232 is the list to empty.
BEHAVIOUR_TOKENS = {
    "dropdown-toggle": "Bootstrap dropdown markup; a theme with a different dropdown DOM overrides the template (#232)",
}


def _tokens(el) -> list[str]:
    return (el.get("class") or "").split()


def _styled(doc):
    """The elements the table styles: those carrying a sentinel class."""
    return [el for el in doc.iter() if isinstance(el.tag, str) and SENTINELS.intersection(_tokens(el))]


def _offenders(doc) -> list[tuple[str, str]]:
    """(tag, token) for every class token on a sentinel-styled element or one of its span descendants that is
    neither a sentinel, nor cv- prefixed, nor an exempted behaviour token. Icons are <i>, so never visited."""
    found = set()
    for el in _styled(doc):
        for node in (el, *el.iter("span")):
            for token in _tokens(node):
                if token in SENTINELS or token.startswith("cv-") or token in BEHAVIOUR_TOKENS:
                    continue
                found.add((node.tag, token))
    return sorted(found)


def _leaf_contract(location: str, mode: str) -> dict:
    """A flat leaf contract with every flag on (the shape of cv_button_data()'s output)."""
    return {
        "cv_location": location,
        "cv_disabled": False,
        "cv_disabled_reason": "",
        "cv_tag": "a",
        "cv_href": "/author/1/detail/",
        "cv_modal": False,
        "cv_modal_size": "",
        "cv_active": True,
        "cv_key": "detail",
        "cv_label": "Details",
        "cv_short_label": "Details",
        "cv_label_mode": mode,
        "cv_title": "Details",
        "cv_icon": "detail",
        "cv_variant": "secondary",
        "cv_flex": location == "card",
    }


FORM_LEAF = "crud_views/tags/button/form.html"
FORM_TYPES = {
    "submit": "submit",
    "cancel": "button",
    "delete": "submit",
    "filter-submit": "submit",
    "filter-reset": "reset",
}


def _form_contract(kind: str, mode: str, **kw) -> dict:
    """Valid raw form data for cv_button_data(ctx, "form"), with an already registered (element) icon."""
    ctx = {
        "cv_key": kind,
        "cv_type": FORM_TYPES[kind],
        "cv_name": "go",
        "cv_value": "Go",
        "cv_id": "submit-id-go",
        "cv_label_mode": mode,
        "cv_icon": "detail",
        "cv_attrs": {"data_cv_cancel_url": "/back/"},
    }
    ctx.update(kw)
    return ctx


def _guard_client(grants) -> Client:
    user = User.objects.create_user(username=f"guard_{uuid.uuid4().hex[:8]}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_button_chain_renders_only_table_classes(monkeypatch):
    from tests.test1.app.models import Author, Publisher
    from tests.test1.app.views import AuthorListView, cv_author, cv_publisher, cv_publisher_order

    author = Author.objects.create(first_name="Douglas", last_name="Adams")
    Publisher.objects.create(name="Penguin")
    # row menus on the author list
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    full = _guard_client([(cv_author, ("view", "add", "change", "delete"))])
    publisher = _guard_client([(cv_publisher, ("view", "add")), (cv_publisher_order, ("view",))])
    pages = [
        (publisher, reverse(cv_publisher.get_router_name("list"))),  # active list button, filter toggle, create
        (full, reverse(cv_author.get_router_name("list"))),  # rows with overflow menus
        (full, reverse(cv_author.get_router_name("card"))),  # the flex=True card action
        (publisher, "/publisher_order/card/?order=name&dir=asc"),  # sort toggles
        (publisher, "/publisher_order/card/?order=name&dir=desc"),
        (full, reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})),
    ]

    offenders: dict[str, list] = {}
    styled: dict[str, int] = {}

    def check(name, doc):
        offenders[name] = _offenders(doc)
        styled[name] = len(_styled(doc))

    # the action and menu leaves serve the variant locations; the form location has its own leaf, checked below
    assert LOCATIONS - {"form"} == VARIANT_LOCATIONS
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=SENTINEL_CLASSES):
        for location in sorted(VARIANT_LOCATIONS):
            for mode in sorted(LABEL_MODES):
                markup = render_to_string("crud_views/tags/button/action.html", _leaf_contract(location, mode))
                check(f"action.html:{location}:{mode}", html.fromstring(f"<div>{markup}</div>"))
            markup = render_to_string("crud_views/tags/button/menu_item.html", _leaf_contract(location, "icon"))
            check(f"menu_item.html:{location}", html.fromstring(f"<div>{markup}</div>"))
        for kind in sorted(FORM_KINDS):
            for mode in sorted(LABEL_MODES):
                markup = render_to_string(FORM_LEAF, cv_button_data(_form_contract(kind, mode), "form"))
                check(f"form.html:{kind}:{mode}", html.fromstring(f"<div>{markup}</div>"))
        for client, url in pages:
            resp = client.get(url)
            assert resp.status_code == 200, url
            check(url, html.fromstring(resp.content))

    assert all(styled.values()), styled  # every render had table-styled elements to check
    assert {name: found for name, found in offenders.items() if found} == {}


@pytest.mark.parametrize("kind", sorted(FORM_KINDS))
@pytest.mark.parametrize("mode", sorted(LABEL_MODES))
def test_form_leaf_classes_and_bodies(kind, mode):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=SENTINEL_CLASSES):
        markup = render_to_string(FORM_LEAF, cv_button_data(_form_contract(kind, mode), "form"))
    (button,) = html.fromstring(f"<div>{markup}</div>").cssselect("button")
    assert _tokens(button) == [SENTINEL_CLASSES[f"form:{kind}"]]
    assert (button.get("type"), button.get("name"), button.get("value")) == (FORM_TYPES[kind], "go", "Go")
    assert button.get("data-cv-cancel-url") == ("/back/" if kind == "cancel" else None)
    hidden = button.cssselect("span." + SENTINEL_CLASSES["form:hidden-label"])
    icons = button.cssselect("i")
    if mode == "icon":
        assert [s.text for s in hidden] == ["Go"]
        assert (button.get("title"), button.get("data-cv-tooltip")) == ("Go", "form")
        assert len(icons) == 1
    elif mode == "both":
        assert not hidden and len(icons) == 1
        assert [s.text for s in button.cssselect("span")] == ["Go"]
        assert button.get("title") is None and button.get("data-cv-tooltip") is None
    else:
        assert not hidden and not icons
        assert [s.text for s in button.cssselect("span")] == ["Go"]
        assert button.get("title") is None and button.get("data-cv-tooltip") is None


# --- the action-only {% cv_button %} tag never renders the form location (L-ACTION-TAG-FORM-ROUTING) -------------

_VALID_FORM_TAG_CONTEXT = {
    "cv_access": True,
    "cv_key": "submit",
    "cv_type": "submit",
    "cv_name": "submit",
    "cv_value": "Save",
    "cv_id": "submit-id-submit",
    "cv_url": "/u/",
    "cv_action_label": "Save",
    "cv_icon_action": "detail",
    "cv_oid": "o1",
}

_TAG_KINDS = ['{% cv_button "form" %}', '{% cv_button "form" "action" %}', '{% cv_button "form" "menu-item" %}']


@pytest.fixture
def tag_spies(monkeypatch):
    from crud_views.templatetags import crud_views as tags

    calls = []
    for name in ("cv_resolve_action", "cv_button_data", "render_to_string"):
        real = getattr(tags, name)

        def spy(*args, _name=name, _real=real, **kwargs):
            calls.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(tags, name, spy)
    return calls


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("tag", _TAG_KINDS)
@pytest.mark.parametrize(
    "ctx", [_VALID_FORM_TAG_CONTEXT, {}, {"cv_key": "submit", "cv_access": False}], ids=["visible", "empty", "hidden"]
)
def test_cv_button_tag_rejects_form_location(tag_spies, tag, ctx, strict):
    template = Template("{% load crud_views %}" + tag)
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="cv_button") as excinfo:
        template.render(Context(dict(ctx)))
    assert "'form'" in str(excinfo.value)
    assert tag_spies == []  # rejected before resolution, normalization and leaf dispatch


def test_direct_form_normalization_still_succeeds():
    data = cv_button_data(_VALID_FORM_TAG_CONTEXT, "form")
    assert (data["cv_location"], data["cv_key"], data["cv_type"]) == ("form", "submit", "submit")
    markup = render_to_string(FORM_LEAF, data)
    (button,) = html.fromstring(f"<div>{markup}</div>").cssselect("button")
    assert (button.get("name"), button.get("value")) == ("submit", "Save")


_ACTION_TAG_CONTEXT = {
    "cv_key": "detail",
    "cv_access": True,
    "cv_url": "/author/1/detail/",
    "cv_action_label": "Details",
    "cv_icon_action": "detail",
    "cv_list_action_method": "get",
    "cv_oid": "author_detail_1",
}


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("location", sorted(VARIANT_LOCATIONS))
def test_cv_button_tag_keeps_action_and_menu_item(tag_spies, location, strict):
    with override_settings(CRUD_VIEWS_STRICT=strict):
        action = Template('{% load crud_views %}{% cv_button "' + location + '" %}').render(
            Context(dict(_ACTION_TAG_CONTEXT))
        )
        item = Template('{% load crud_views %}{% cv_button "' + location + '" "menu-item" %}').render(
            Context(dict(_ACTION_TAG_CONTEXT))
        )
        hidden = Template('{% load crud_views %}{% cv_button "' + location + '" %}').render(
            Context({"cv_key": "detail", "cv_access": False, "cv_url": "/x/"})
        )
    assert html.fromstring(f"<div>{action}</div>").cssselect('a[href="/author/1/detail/"]')
    assert html.fromstring(f"<div>{item}</div>").cssselect('a[href="/author/1/detail/"]')
    assert hidden == ""
    assert "cv_button_data" in tag_spies and "render_to_string" in tag_spies
