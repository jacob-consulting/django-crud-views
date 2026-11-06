"""Card inheritance, escaped insertion slots, action plumbing and unchanged default rendering."""

import re
import uuid
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from django.contrib.auth.models import User
from django.template import engines
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, cv_author

# a menu next to the inline buttons, so the card_actions block carries both the menu forms and the container
ACTIONS = [*AuthorCardListView.cv_card_actions, CardAction(key="ping", label="Ping")]

# Frozen from f700a0b4^, before either insertion block existed. Keep whitespace verbatim.
CARD_TEMPLATE_BEFORE_INSERTION = """{% load crud_views %}
{% cv_card_action_group object as group %}

<div class="{% cv_button_class "card" "root" %}">
    <div class="{% cv_button_class "card" "body" %}">
        {% cv_button_class "card" "title" as cv_card_title_class %}{% cv_heading level=5 class=cv_card_title_class %}{% block card_title %}{{ object }}{% endblock card_title %}{% endcv_heading %}
        {% block card_content %}{% endblock card_content %}
        {% block card_actions %}
        {% for ctx in group.menu %}
            {% cv_render_list_action_form ctx %}
        {% endfor %}
        {% include "crud_views/tags/button/container.html" with cv_buttons=group.inline cv_group=group cv_location="card" %}
        {% endblock card_actions %}
    </div>
</div>
"""  # noqa: E501 -- frozen template bytes must retain their original line lengths


@pytest.fixture
def client_full() -> Client:
    user = User.objects.create_user(username=f"card_243_{uuid.uuid4().hex[:8]}", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def actions(monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", ACTIONS)
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "update"])


def _card(client):
    resp = client.get(reverse(cv_author.get_router_name("card")))
    assert resp.status_code == 200
    (card,) = lxml_html.fromstring(resp.content).cssselect(".row > div > div")
    return card


def _markup(element) -> str:
    return _mask_csrf(lxml_html.tostring(element, encoding="unicode"))


def _mask_csrf(markup):
    # The CSRF token is masked differently on every render; preserve every other byte.
    return re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]*"', r'\1CSRF"', markup)


def _assert_actions(card, author):
    (container,) = card.cssselect("[cv-card-container]")
    for key in ("detail", "update"):
        (link,) = container.cssselect(f'a[cv-key="{key}"]')
        assert urlsplit(link.get("href")).path == reverse(cv_author.get_router_name(key), kwargs={"pk": author.pk})
        assert not link.xpath('ancestor::*[contains(@class, "dropdown-menu")]')

    triggers = container.cssselect('.dropdown-menu [data-cv-action="submit-form"]')
    assert triggers
    assert {trigger.get("cv-key") for trigger in triggers} == {"ping"}
    forms = card.cssselect("form[hidden]")
    assert len(forms) == len(triggers)
    for trigger in triggers:
        (form,) = [form for form in forms if form.get("id") == trigger.get("data-cv-target")]
        assert form.get("method").lower() == "post"
        assert form.get("action") == reverse(cv_author.get_router_name(trigger.get("cv-key")), kwargs={"pk": author.pk})
        (csrf,) = form.cssselect('input[type="hidden"][name="csrfmiddlewaretoken"]')
        assert csrf.get("value")


@pytest.mark.django_db
def test_extending_template_fills_content_and_keeps_actions(client_full, actions, author_douglas_adams, monkeypatch):
    stock = _markup(_card(client_full))

    monkeypatch.setattr(AuthorCardListView, "cv_card_template", "app/author_card_blocks.html")
    card = _card(client_full)
    (content,) = card.cssselect("p.cv-test-content")
    assert content.text == "Adams"
    assert len(card.cssselect("[cv-card-container]")) == 1
    _assert_actions(card, author_douglas_adams)
    # drop_tree retains tails: only the inserted elements disappear, not stock whitespace.
    for inserted in card.cssselect(".cv-test-root, .cv-test-header, .cv-test-content"):
        inserted.drop_tree()
    assert _markup(card) == stock


@pytest.mark.django_db
@pytest.mark.parametrize("text", ["Douglas", '<em data-injected="yes">Douglas & Adams</em>'])
def test_insertion_blocks_positions_and_escaping(client_full, actions, author_douglas_adams, monkeypatch, text):
    author_douglas_adams.pseudonym = text
    author_douglas_adams.save(update_fields=["pseudonym"])
    monkeypatch.setattr(AuthorCardListView, "cv_card_template", "app/author_card_blocks.html")

    card = _card(client_full)
    roots = card.cssselect(".cv-test-root")
    headers = card.cssselect(".cv-test-header")
    assert len(roots) == 1
    assert len(headers) == 1
    root, header = roots[0], headers[0]
    (body,) = card.cssselect(".card-body")
    (heading,) = body.cssselect("h5")
    assert card[0] is root
    assert root.getparent() is card
    assert header.getparent() is body
    assert body.index(header) < body.index(heading)
    assert header not in heading.iterdescendants()
    for inserted in (root, header):
        assert inserted.text == text
        assert len(inserted) == 0
    assert heading.text == "Douglas Adams"
    assert card.cssselect(".cv-test-content")[0].text == "Adams"
    assert card.cssselect("[cv-card-container]")
    assert card.cssselect("form")


@pytest.mark.django_db
def test_unused_insertion_blocks_preserve_bytes(client_full, actions, author_douglas_adams):
    response = client_full.get(reverse(cv_author.get_router_name("card")))
    assert response.status_code == 200
    request = response.wsgi_request
    context = {"object": author_douglas_adams, "view": response.context["view"], "request": request}
    backend = engines["django"]
    before = backend.from_string(CARD_TEMPLATE_BEFORE_INSERTION).render(context, request=request)
    current = backend.get_template("crud_views/tags/card.html").render(context, request=request)
    for raw in (before, current):
        _assert_actions(lxml_html.fromstring(raw), author_douglas_adams)
    assert _mask_csrf(before) == _mask_csrf(current)


@pytest.mark.django_db
def test_documented_insertion_blocks(client_full, actions, author_douglas_adams, monkeypatch, settings):
    reference = Path(__file__).resolve().parents[2] / "docs/reference/card-list-view.md"
    match = re.search(r"<!-- card-recipe: insertion-blocks -->\n```html\n(.*?)\n```", reference.read_text(), re.S)
    assert match is not None, "Publish the marked insertion-blocks inheritance recipe"
    template_name = "app/documented_card_insertions.html"
    templates = deepcopy(settings.TEMPLATES)
    templates[0]["APP_DIRS"] = False
    templates[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {template_name: match[1]}),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = templates
    text = '<em data-injected="yes">Douglas & "Adams"</em>'
    author_douglas_adams.pseudonym = text
    author_douglas_adams.save(update_fields=["pseudonym"])
    monkeypatch.setattr(AuthorCardListView, "cv_card_template", template_name)

    card = _card(client_full)
    (root,) = card.cssselect(".author-card-status")
    (header,) = card.cssselect(".author-card-intro")
    (body,) = card.cssselect(".card-body")
    (heading,) = body.cssselect("h5")
    assert card[0] is root
    assert root.getparent() is card
    assert header.getparent() is body
    assert body.index(header) < body.index(heading)
    assert header not in heading.iterdescendants()
    for inserted in (root, header):
        assert inserted.text == text
        assert len(inserted) == 0
    assert heading.text == "Douglas Adams"
    _assert_actions(card, author_douglas_adams)


@pytest.mark.django_db
@override_settings(
    CRUD_VIEWS_BUTTON_CLASSES={"card:root": "theme-card", "card:body": "theme-body", "card:title": "theme-title h3"}
)
def test_class_keys(client_full, author_douglas_adams):
    card = _card(client_full)
    assert card.get("class") == "theme-card"
    (body,) = card.cssselect(".theme-body")
    (title,) = body.cssselect("h5")
    assert title.get("class") == "theme-title h3"
    assert title.text == "Douglas Adams"
