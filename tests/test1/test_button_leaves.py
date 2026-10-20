"""Button leaves: presentation-only templates fed the flat leaf contract, thin logic templates, one container."""

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib import button_classes
from crud_views.lib.button_classes import register_button_classes
from crud_views.lib.view import CardAction, ContextButton
from crud_views.lib.view.action_menu import ActionGroup
from crud_views.lib.view.button_data import LEAF_KEYS
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, AuthorDetailView, AuthorListView, cv_author

ACTION_LEAF = "crud_views/tags/button/action.html"
MENU_ITEM_LEAF = "crud_views/tags/button/menu_item.html"
CONTAINER_LEAF = "crud_views/tags/button/container.html"


def _context_get(**extra) -> dict:
    data = {
        "cv_location": "context",
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
        "cv_label_visible": False,
        "cv_title": "Details",
        "cv_icon": "detail",
        "cv_variant": "secondary",
        "cv_flex": False,
    }
    data.update(extra)
    return data


def _one(markup: str, selector: str):
    doc = lxml_html.fromstring(f"<div>{markup}</div>")
    nodes = doc.cssselect(selector)
    assert len(nodes) == 1, markup
    return nodes[0]


def test_action_leaf_renders_from_contract_only():
    markup = render_to_string(ACTION_LEAF, _context_get())
    a = _one(markup, "a")
    assert a.get("href") == "/author/1/detail/"
    assert a.get("class") == "btn btn-outline-primary btn-lg active"
    assert a.get("aria-current") == "page"
    assert a.get("title") == "Details"
    assert a.get("cv-key") == "detail"
    assert len(a.cssselect("i")) == 1
    assert len(a.cssselect("span.visually-hidden")) == 1

    card = _context_get(cv_location="card", cv_active=False, cv_label_visible=True, cv_variant="primary")
    del card["cv_title"]
    a = _one(render_to_string(ACTION_LEAF, card), "a")
    assert lxml_html.tostring(a.cssselect("span")[0], encoding="unicode") == "<span>Details</span>"
    assert not a.cssselect("i")
    assert a.get("title") is None

    post = _context_get(cv_tag="button", cv_active=False, cv_submit_target="cv_form_o1")
    del post["cv_href"]
    button = _one(
        render_to_string(ACTION_LEAF, post),
        "button[type=button][data-cv-action=submit-form][data-cv-target=cv_form_o1]",
    )
    assert button.get("href") is None

    disabled = _context_get(cv_tag="button", cv_active=False, cv_disabled=True, cv_disabled_reason="permission")
    del disabled["cv_href"]
    button = _one(render_to_string(ACTION_LEAF, disabled), "button[disabled][data-cv-disabled=permission]")
    assert button.get("data-cv-modal") is None
    assert button.get("data-cv-modal-size") is None
    assert button.get("data-cv-action") is None


def test_action_leaf_with_empty_variant_class():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary": None}):
        markup = render_to_string(ACTION_LEAF, _context_get())
    assert _one(markup, "a").get("class").strip() == "active"
    assert "None" not in markup


def test_menu_item_leaf_title_only_for_context():
    item = _context_get(cv_location="list", cv_active=False)
    assert _one(render_to_string(MENU_ITEM_LEAF, item), "a.dropdown-item").get("title") is None
    item["cv_location"] = "context"
    assert _one(render_to_string(MENU_ITEM_LEAF, item), "a.dropdown-item").get("title") == "Details"


def test_container_div_has_no_aria_label():
    ctx = {"cv_container_tag": "div", "cv_location": "card", "cv_buttons": [], "cv_group": ActionGroup()}
    div = _one(render_to_string(CONTAINER_LEAF, ctx), "div[cv-card-container]")
    assert div.get("class") == "d-flex gap-2"
    assert div.get("cv-card-container") == "true"
    assert div.get("aria-label") is None

    ctx = {"cv_container_tag": "fieldset", "cv_location": "list", "cv_buttons": [], "cv_group": ActionGroup()}
    fieldset = _one(render_to_string(CONTAINER_LEAF, ctx), "fieldset")
    assert fieldset.get("aria-label") == "Actions"
    assert fieldset.get("cv-list-container") == "true"


# --- through the views --------------------------------------------------------------------------------------------


@pytest.fixture
def client_full(db) -> Client:
    user = User.objects.create_user(username="leaves_full", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def theme_layer():
    saved = dict(button_classes._THEME_BUTTON_CLASSES)
    yield
    button_classes._THEME_BUTTON_CLASSES.clear()
    button_classes._THEME_BUTTON_CLASSES.update(saved)
    button_classes.reset_button_classes_cache()


def _get(client, name, **kwargs):
    resp = client.get(reverse(cv_author.get_router_name(name), kwargs=kwargs or None))
    assert resp.status_code == 200
    return resp, lxml_html.fromstring(resp.content)


def _toolbar(doc):
    return doc.cssselect("fieldset[cv-context-container]")[0]


def _with_ping(monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [*AuthorCardListView.cv_card_actions, CardAction(key="ping", label="Ping")],
    )


@pytest.mark.django_db
def test_group_always_returned(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", None)
    resp, doc = _get(client_full, "list")
    group = resp.context["view"].cv_get_list_action_group(author_douglas_adams)
    assert isinstance(group, ActionGroup)
    assert len(group.inline) == 3
    assert group.menu == []
    assert not doc.cssselect(".cv-menu-toggle")

    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", None)
    resp, doc = _get(client_full, "detail", pk=author_douglas_adams.pk)
    group = resp.context["view"].cv_get_context_action_group(author_douglas_adams)
    assert isinstance(group, ActionGroup)
    assert group.inline
    assert group.menu == []
    assert not doc.cssselect(".cv-menu-toggle")

    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", None)
    resp, doc = _get(client_full, "card")
    group = resp.context["view"].cv_get_card_action_group(author_douglas_adams)
    assert isinstance(group, ActionGroup)
    assert len(group.inline) == len(AuthorCardListView.cv_card_actions)
    assert group.menu == []
    assert not doc.cssselect(".cv-menu-toggle")


@pytest.mark.django_db
def test_card_post_action_is_a_button(client_full, author_douglas_adams, monkeypatch):
    _with_ping(monkeypatch)
    _, doc = _get(client_full, "card")
    row = doc.cssselect(".card.mb-3 .d-flex.gap-2")[0]
    buttons = row.cssselect("button[data-cv-action='submit-form']")
    assert len(buttons) == 1
    assert buttons[0].get("href") is None
    assert not row.cssselect("a[href='#']")
    form = row.cssselect(f"form#{buttons[0].get('data-cv-target')}")[0]
    children = list(row)
    assert children.index(form) < children.index(buttons[0])
    assert all(b.get("cv-key") for b in row.cssselect("a, button"))


@pytest.mark.django_db
def test_card_menu_forms_before_row(client_full, author_douglas_adams, monkeypatch):
    _with_ping(monkeypatch)
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail"])
    _, doc = _get(client_full, "card")
    form = doc.cssselect("form[id^='cv_form_author_ping_']")
    assert len(form) == 1
    row = doc.cssselect(".card.mb-3 .d-flex.gap-2")[0]
    assert form[0] not in row.iter()
    assert form[0] in list(row.itersiblings(preceding=True))


@pytest.mark.django_db
def test_active_context_button_has_aria_current(client_full, author_douglas_adams):
    _, doc = _get(client_full, "detail", pk=author_douglas_adams.pk)
    toolbar = _toolbar(doc)
    detail = toolbar.cssselect("a[cv-key=detail]")[0]
    assert detail.get("aria-current") == "page"
    assert "active" in detail.get("class").split()
    update = toolbar.cssselect("a[cv-key=update]")[0]
    assert update.get("aria-current") is None
    assert "active" not in update.get("class").split()


PILL = ContextButton(
    key="pill",
    key_target="update",
    template_code='<a href="{{ cv_url }}" class="pill" cv-key="{{ cv_key }}">{% load crud_views %}'
    "{% cv_icon cv_icon_action %}{{ cv_action_label }}</a>",
)


@pytest.mark.django_db
@pytest.mark.parametrize("inline", [None, ["detail"]])
def test_custom_template_button_in_container(client_full, author_douglas_adams, monkeypatch, inline):
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [*(AuthorDetailView.cv_context_buttons or []), PILL])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", [*AuthorDetailView.cv_context_actions, "pill"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)
    _, doc = _get(client_full, "detail", pk=author_douglas_adams.pk)
    toolbar = _toolbar(doc)
    pill = [a for a in toolbar if a.get("class") == "pill"]
    assert len(pill) == 1, "the custom button is a direct child of the container, not folded into the menu"
    # ContextButton data carries the target view's key, so {{ cv_key }} in the button's own template is "update"
    assert pill[0].get("cv-key") == "update"
    assert pill[0].get("href") == reverse(cv_author.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    assert pill[0].cssselect("i")
    assert toolbar.cssselect("a[cv-key=detail]")


@pytest.mark.django_db
def test_theme_registration_changes_rendered_classes(client_full, author_douglas_adams, theme_layer):
    register_button_classes({"list:secondary": "btn btn-ghost"})
    _, doc = _get(client_full, "list")
    assert doc.cssselect("fieldset[cv-list-container] a[cv-key=detail]")[0].get("class") == "btn btn-ghost"

    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:secondary": "btn btn-x"}):
        _, doc = _get(client_full, "list")
    assert doc.cssselect("fieldset[cv-list-container] a[cv-key=detail]")[0].get("class") == "btn btn-x"


def test_no_raw_keys_reach_leaves(monkeypatch):
    from crud_views.templatetags import crud_views as tags

    calls = []
    real = tags.render_to_string

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(tags, "render_to_string", spy)
    raw = {
        "cv_key": "detail",
        "cv_access": True,
        "cv_url": "/author/1/detail/",
        "cv_action_label": "Details",
        "cv_icon_action": "detail",
        "cv_list_action_method": "get",
        "cv_template_code": "<b>never</b>",
        "cv_oid": "author_detail_1",
    }
    markup = Template('{% load crud_views %}{% cv_button "context" %}').render(Context(raw))
    assert "cv-key" in markup
    assert calls
    for args, kwargs in calls:
        assert set(kwargs.get("context") or args[1]) <= LEAF_KEYS


def test_hidden_action_renders_nothing():
    # cv_list_action / cv_card_action hand {} to the thin templates for a hidden action; unresolved data the user
    # may not use is hidden too, as the old template branches did
    tpl = Template('{% load crud_views %}{% cv_button "list" %}')
    assert tpl.render(Context({})) == ""
    assert tpl.render(Context({"cv_key": "update", "cv_access": False, "cv_url": "/x/"})) == ""
