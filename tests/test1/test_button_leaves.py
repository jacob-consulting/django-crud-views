"""Button leaves: presentation-only templates fed the flat leaf contract, thin logic templates, one container."""

import pytest
from django.conf import settings
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
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDetailView,
    AuthorListView,
    PublisherListView,
    cv_author,
    cv_publisher,
)

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
        "cv_label_mode": "icon",
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

    card = _context_get(cv_location="card", cv_active=False, cv_label_mode="label", cv_variant="primary")
    del card["cv_title"]
    a = _one(render_to_string(ACTION_LEAF, card), "a")
    assert lxml_html.tostring(a.cssselect("span")[0], encoding="unicode") == "<span>Details</span>"
    assert not a.cssselect("i")
    assert a.get("title") is None

    both = {**card, "cv_label_mode": "both"}
    a = _one(render_to_string(ACTION_LEAF, both), "a")
    assert len(a.cssselect("i")) == 1
    assert lxml_html.tostring(a.cssselect("span")[0], encoding="unicode") == "<span>Details</span>"
    assert not a.cssselect("span.visually-hidden")
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


def test_active_and_flex_come_from_the_table(theme_layer):
    register_button_classes({"context:active": "is-active", "card:active": "is-current", "card:flex": "is-expanded"})
    a = _one(render_to_string(ACTION_LEAF, _context_get()), "a")
    assert a.get("class") == "btn btn-outline-primary btn-lg is-active"
    card = _context_get(cv_location="card", cv_variant="primary", cv_flex=True)
    a = _one(render_to_string(ACTION_LEAF, card), "a")
    assert a.get("class") == "btn btn-primary btn-sm is-current is-expanded"


def test_menu_item_active_comes_from_the_table(theme_layer):
    register_button_classes({"menu:active": "is-active"})
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_location="list")), "a")
    assert a.get("class") == "dropdown-item is-active"


@pytest.mark.parametrize(
    ("key", "extra", "base"),
    [
        ("context:active", {}, ["btn", "btn-outline-primary", "btn-lg"]),
        (
            "card:flex",
            {"cv_location": "card", "cv_variant": "primary", "cv_active": False, "cv_flex": True},
            ["btn", "btn-primary", "btn-sm"],
        ),
    ],
)
def test_utility_key_set_to_none_renders_no_token(key, extra, base):
    # the flag is on, the key is None, so only the base classes render (a trailing space is fine)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: None}):
        a = _one(render_to_string(ACTION_LEAF, _context_get(**extra)), "a")
    assert a.get("class").split() == base


def test_hidden_label_comes_from_the_table(theme_layer):
    register_button_classes({"list:hidden-label": "sr-only"})
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_location="list", cv_active=False)), "a")
    (hidden,) = a.cssselect("span")
    assert hidden.get("class") == "sr-only"
    assert hidden.text == "Details"


def test_menu_item_without_icon_renders_the_fixed_width_placeholder():
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_location="list", cv_active=False, cv_icon=None)), "a")
    (placeholder,) = a.cssselect("span")
    assert placeholder.get("class") == "cv-icon-fw"
    assert placeholder.get("aria-hidden") == "true"


@pytest.mark.django_db
def test_toggles_hidden_label_comes_from_the_table(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    user = User.objects.create_user(username="leaves_publisher_view", password="pw")
    user_viewset_permission(user, cv_publisher, "view")
    publisher_client = Client()
    publisher_client.force_login(user)
    classes = {"list:hidden-label": "sr-only", "context:hidden-label": "sr-label"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        _, doc = _get(client_full, "list")
        resp = publisher_client.get(reverse(cv_publisher.get_router_name("list")))
    menu_toggle = doc.cssselect("fieldset[cv-list-container] button.cv-menu-toggle")[0]
    assert menu_toggle.cssselect("span")[0].get("class") == "sr-only"
    assert resp.status_code == 200
    filter_toggle = lxml_html.fromstring(resp.content).cssselect("#cv-filter-toggle")[0]
    assert filter_toggle.cssselect("span")[-1].get("class") == "sr-label"


@pytest.mark.django_db
def test_card_icon_mode_hidden_label_comes_from_the_table(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label_mode="icon")])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:hidden-label": "sr-only"}):
        _, doc = _get(client_full, "card")
    a = doc.cssselect("div[cv-card-container] a[cv-key=detail]")[0]
    assert a.cssselect("span")[0].get("class") == "sr-only"


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


# the 0.30 body of tags/actions_menu_item.html, as a project override of it still looks: raw keys, shared label include
MENU_ITEM_030 = """{% if cv_disabled %}
<button type="button" class="dropdown-item" disabled
    data-cv-disabled="{{ cv_disabled_reason }}"
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</button>
{% elif cv_modal %}
<a class="dropdown-item" href="{{ cv_url }}"
    data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</a>
{% elif cv_list_action_method == "post" %}
<button type="button" class="dropdown-item"
    data-cv-action="submit-form" data-cv-target="cv_form_{{ cv_oid }}"
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</button>
{% else %}
<a class="dropdown-item{% if cv_is_active %} active{% endif %}" href="{{ cv_url }}"
    {% if cv_is_active %}aria-current="page"{% endif %}
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</a>
{% endif %}"""


@pytest.mark.parametrize(
    "extra, label",
    [
        ({"cv_location": "list"}, "Det"),
        ({"cv_location": "list", "cv_action_short_label": None}, "Details"),
        ({"cv_location": "card", "cv_label": "Card label"}, "Card label"),
    ],
)
def test_legacy_menu_item_override_keeps_icon_and_label(extra, label):
    raw = {
        "cv_key": "detail",
        "cv_access": True,
        "cv_url": "/author/1/detail/",
        "cv_icon_action": "detail",
        "cv_action_short_label": "Det",
        "cv_action_label": "Details",
        "cv_list_action_method": "get",
        "cv_oid": "author_detail_1",
        **extra,
    }
    a = _one(Template(MENU_ITEM_030).render(Context(raw)), "a.dropdown-item")
    assert len(a.cssselect("i")) == 1
    assert a.text_content().strip() == label


def test_menu_item_leaf_label_from_contract():
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_short_label="Det")), "a.dropdown-item")
    assert len(a.cssselect("i")) == 1
    assert a.text_content().strip() == "Det"
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_icon="")), "a.dropdown-item")
    assert not a.cssselect("i")
    assert len(a.cssselect("span.cv-icon-fw[aria-hidden=true]")) == 1


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


_PROCESSOR_CALLS = []


def counting_processor(request) -> dict:
    _PROCESSOR_CALLS.append(request.path)
    return {}


def _processor_calls(client, name) -> tuple[int, int]:
    """Context processor runs and inline row buttons of one page."""
    templates = [{**t, "OPTIONS": {**t["OPTIONS"]}} for t in settings.TEMPLATES]
    processors = templates[0]["OPTIONS"]["context_processors"]
    templates[0]["OPTIONS"]["context_processors"] = [*processors, f"{__name__}.counting_processor"]
    _PROCESSOR_CALLS.clear()
    with override_settings(TEMPLATES=templates):
        _, doc = _get(client, name)
    buttons = doc.cssselect("[cv-list-container] > [cv-key], [cv-card-container] > [cv-key]")
    return len(_PROCESSOR_CALLS), len(buttons)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, view, attr",
    [("list", AuthorListView, "cv_list_actions_inline"), ("card", AuthorCardListView, "cv_card_actions_inline")],
)
def test_inline_buttons_do_not_rerun_context_processors(
    client_full, author_douglas_adams, monkeypatch, name, view, attr
):
    # table cells and cards render per row on their own; the inline buttons must add no processor runs on top
    from tests.test1.app.models import Author

    for i in range(3):
        Author.objects.create(first_name="Extra", last_name=f"Author {i}")
    monkeypatch.setattr(view, attr, [])
    calls_without, buttons_without = _processor_calls(client_full, name)
    monkeypatch.setattr(view, attr, ["detail", "update", "delete"])
    calls_with, buttons_with = _processor_calls(client_full, name)
    assert buttons_without == 0
    assert buttons_with == 12
    assert calls_with == calls_without


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
    token = form.cssselect("input[name=csrfmiddlewaretoken]")
    assert len(token) == 1 and token[0].get("value")
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


def _publisher_list(client):
    """The publisher list is the one stock page whose toolbar has a filter toggle."""
    resp = client.get(reverse(cv_publisher.get_router_name("list")))
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content)


@pytest.mark.django_db
def test_filter_toggle_carries_its_own_key(client_user_publisher_view):
    # the toggle has no target view, so cv-key is the button's own key (#208)
    toggle = _toolbar(_publisher_list(client_user_publisher_view)).cssselect("button#cv-filter-toggle")
    assert len(toggle) == 1
    assert toggle[0].get("cv-key") == "filter"


@pytest.mark.django_db
@pytest.mark.parametrize("inline", [None, ["list"]])
def test_every_context_action_has_a_key(client_user_publisher_view, monkeypatch, inline):
    """Inline or folded into the menu, every action in the toolbar is selectable by its key (#208)."""
    monkeypatch.setattr(PublisherListView, "cv_context_actions_inline", inline)
    toolbar = _toolbar(_publisher_list(client_user_publisher_view))
    # the overflow menu toggle is a disclosure control, not an action, and carries no key
    actions = [b for b in toolbar.cssselect("a, button") if "cv-menu-toggle" not in (b.get("class") or "").split()]
    assert len(actions) > 1
    assert all(b.get("cv-key") for b in actions), [(b.tag, b.get("cv-key")) for b in actions]


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


@pytest.mark.parametrize("location", ["context", "list", "card"])
def test_action_leaf_marks_tooltip_exactly_when_title_is_set(location):
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_location=location)), "a")
    assert a.get("title") == "Details"
    assert a.get("data-cv-tooltip") == location

    labelled = _context_get(cv_location=location, cv_label_mode="label")
    del labelled["cv_title"]
    a = _one(render_to_string(ACTION_LEAF, labelled), "a")
    assert a.get("title") is None
    assert a.get("data-cv-tooltip") is None


def test_action_leaf_empty_title_renders_no_marker():
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_title="", cv_label="")), "a")
    assert a.get("title") is None
    assert a.get("data-cv-tooltip") is None


def test_menu_item_leaf_has_no_tooltip_marker():
    item = _context_get(cv_location="context", cv_active=False)
    assert _one(render_to_string(MENU_ITEM_LEAF, item), "a.dropdown-item").get("data-cv-tooltip") is None


# host-placed icons on the menu and filter toggles (#258)

host_icons = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS)
FILTER_TOGGLE = "crud_views/tags/context_action_filter.html"


def _filter_toggle(expanded: bool):
    ctx = {"cv_filter_expanded": expanded, "cv_action_label": "Filter", "cv_key": "filter"}
    return _one(render_to_string(FILTER_TOGGLE, ctx), "button#cv-filter-toggle")


@pytest.mark.django_db
@host_icons
def test_host_menu_toggle(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    _, doc = _get(client_full, "list")
    toggle = doc.cssselect("fieldset[cv-list-container] button.cv-menu-toggle")[0]
    assert "icon-dots" in toggle.get("class").split()
    assert not toggle.cssselect("i")
    assert toggle.cssselect("span.visually-hidden")[0].text == "More actions"


@pytest.mark.django_db
def test_element_menu_toggle_unchanged(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    _, doc = _get(client_full, "list")
    toggle = doc.cssselect("fieldset[cv-list-container] button.cv-menu-toggle")[0]
    assert toggle.cssselect("i")[0].get("class") == "fa-solid fa-ellipsis"


@host_icons
def test_host_filter_toggle_closed():
    button = _filter_toggle(False)
    classes = button.get("class").split()
    assert "icon-funnel" in classes and "icon-x" not in classes
    assert button.get("data-cv-filter-icon-open") == "icon-funnel"
    assert button.get("data-cv-filter-icon-close") == "icon-x"
    assert not button.cssselect("[data-cv-filter-icon]")
    assert not button.cssselect("i")
    assert button.cssselect("span")[-1].text == "Filter"


@host_icons
def test_host_filter_toggle_open():
    classes = _filter_toggle(True).get("class").split()
    assert "icon-x" in classes and "icon-funnel" not in classes


@host_icons
def test_filter_toggle_mixed_placement_uses_spans():
    with override_settings(CRUD_VIEWS_ICONS={**HOST_ICONS, "filter-close": "fas:xmark"}):
        button = _filter_toggle(False)
    assert button.get("data-cv-filter-icon-open") is None
    assert len(button.cssselect("[data-cv-filter-icon]")) == 2
    assert button.cssselect('[data-cv-filter-icon="open"] i')[0].get("class") == "icon icon-funnel"


def test_leaf_dict_without_icon_inline_keeps_the_icon():
    # a hand-built leaf dict from before #258 has no cv_icon_inline: a missing key means inline, not "no icon"
    ctx = {k: v for k, v in _context_get().items() if k != "cv_icon_inline"}
    assert len(_one(render_to_string(ACTION_LEAF, ctx), "a").cssselect("i")) == 1
    both = {**ctx, "cv_label_mode": "both"}
    assert len(_one(render_to_string(ACTION_LEAF, both), "a").cssselect("i")) == 1
    item = _one(render_to_string(MENU_ITEM_LEAF, {**ctx, "cv_location": "list"}), "a")
    assert len(item.cssselect("i.cv-icon-fw")) == 1
    placeholder = _one(render_to_string(MENU_ITEM_LEAF, {**ctx, "cv_location": "list", "cv_icon": None}), "a")
    assert placeholder.cssselect("span")[0].get("class") == "cv-icon-fw"


def test_menu_toggle_without_inline_key_keeps_the_icon():
    ctx = {"cv_location": "list", "cv_menu_icon": "actions-menu"}
    toggle = _one(render_to_string("crud_views/tags/actions_menu_toggle.html", ctx), "button")
    assert toggle.cssselect("i")[0].get("class") == "fa-solid fa-ellipsis"
