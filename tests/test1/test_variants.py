"""Semantic button variants: cv_action_variant, ContextButton.variant, CardAction.variant and viewset.E209."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from lxml import html

from crud_views.lib.view import CardAction, ChildContextButton, ContextButton
from crud_views.lib.view.buttons import FilterContextButton
from crud_views.lib.view.variant import VARIANTS, Variant, is_variant
from crud_views.lib.views import CardListView, CreateView, DeleteView, DetailView, ListView, UpdateView
from crud_views.lib.views.action_ordered import OrderedUpView
from crud_views.lib.views.manage import ManageView
from crud_views_polymorphic.lib.create_select import PolymorphicCreateSelectView
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDetailView,
    AuthorUpdateView,
    PublisherCardListView,
    PublisherListView,
)

E209 = "viewset.E209"


def e209(checks) -> list[str]:
    return [m.msg for c in checks for m in c.messages() if m.id == E209]


def _client(viewset, perms) -> Client:
    user = User.objects.create_user(username=f"variants_{uuid.uuid4().hex[:8]}", password="pw")
    for perm in perms:
        user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def test_view_defaults():
    assert CreateView.cv_action_variant == "primary"
    assert PolymorphicCreateSelectView.cv_action_variant == "primary"
    assert DeleteView.cv_action_variant == "danger"
    for cls in (UpdateView, DetailView, ListView, OrderedUpView, ManageView, CardListView):
        assert cls.cv_action_variant == "secondary", cls
    assert Variant.DANGER == "danger"
    assert {"primary", "secondary", "tertiary", "danger"} == VARIANTS
    assert is_variant("danger") and not is_variant("huge") and not is_variant(None)


@pytest.mark.django_db
def test_cv_get_dict_carries_variant(cv_author, author_douglas_adams):
    client = _client(cv_author, ["view", "add", "change", "delete"])
    response = client.get("/author/")
    view = response.context["view"]
    resolved = view.cv_resolved_actions(["detail", "update", "delete"], author_douglas_adams)
    assert [ctx["cv_variant"] for _, ctx in resolved] == ["secondary", "secondary", "danger"]


@pytest.mark.django_db
def test_context_button_override(cv_author, cv_publisher, author_douglas_adams, publisher_penguin):
    client = _client(cv_author, ["view", "change"])
    view = client.get(f"/author/{author_douglas_adams.pk}/detail/").context["view"]
    ctx = view.cv_get_view_context(object=author_douglas_adams)
    assert ContextButton(key="x", key_target="update", variant="danger").get_context(ctx)["cv_variant"] == "danger"
    assert ContextButton(key="x", key_target="update").get_context(ctx)["cv_variant"] == "secondary"

    client = _client(cv_publisher, ["view"])
    view = client.get(f"/publisher/{publisher_penguin.pk}/detail/").context["view"]
    ctx = view.cv_get_view_context(object=publisher_penguin)
    assert ChildContextButton(key="b", child_name="book").get_context(ctx)["cv_variant"] == "secondary"
    button = ChildContextButton(key="b", child_name="book", variant="primary")
    assert button.get_context(ctx)["cv_variant"] == "primary"


@pytest.mark.django_db
def test_filter_button_override(cv_publisher, monkeypatch):
    client = _client(cv_publisher, ["view"])
    view = client.get("/publisher/").context["view"]
    ctx = view.cv_get_view_context()
    assert "cv_variant" not in FilterContextButton().get_context(ctx)
    assert FilterContextButton(variant="primary").get_context(ctx)["cv_variant"] == "primary"

    def toggle_class() -> str:
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:primary": "x-primary"}):
            doc = html.fromstring(client.get("/publisher/").content)
        return doc.cssselect("#cv-filter-toggle")[0].get("class")

    assert "x-primary" not in toggle_class()
    monkeypatch.setattr(PublisherListView, "cv_context_buttons", [FilterContextButton(variant="primary")])
    assert toggle_class() == "x-primary"


@pytest.mark.django_db
def test_card_action_fallback(cv_author, cv_publisher, author_douglas_adams, publisher_penguin):
    client = _client(cv_author, ["view", "delete"])
    view = client.get("/author/card/").context["view"]
    assert isinstance(view, AuthorCardListView)
    user = view.request.user
    data = view.cv_get_card_action_data(CardAction(key="delete", no_label=True), author_douglas_adams, user)
    assert data["cv_variant"] == "danger"
    action = CardAction(key="delete", no_label=True, variant="tertiary")
    assert view.cv_get_card_action_data(action, author_douglas_adams, user)["cv_variant"] == "tertiary"

    client = _client(cv_publisher, ["view"])
    view = client.get("/publisher/card/").context["view"]
    assert isinstance(view, PublisherCardListView)
    action = CardAction(child_name="book", child_key="list")
    assert view.cv_get_card_action_data(action, publisher_penguin, view.request.user)["cv_variant"] == "secondary"


def test_e209_view(monkeypatch):
    assert e209(AuthorUpdateView.checks()) == []
    monkeypatch.setattr(AuthorUpdateView, "cv_action_variant", "huge")
    messages = e209(AuthorUpdateView.checks())
    assert messages
    assert "'huge'" in messages[0]


def test_e209_context_button(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [ContextButton(key="x", key_target="update")])
    assert e209(AuthorDetailView.checks()) == []
    monkeypatch.setattr(
        AuthorDetailView, "cv_context_buttons", [ContextButton(key="x", key_target="update", variant="nope")]
    )
    messages = e209(AuthorDetailView.checks())
    assert messages
    assert "'nope'" in messages[0]
    assert "context button 'x'" in messages[0]


def test_e209_card_action(monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", variant="primary")])
    assert e209(AuthorCardListView.checks()) == []
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", variant="loud")])
    messages = e209(AuthorCardListView.checks())
    assert messages
    assert "'loud'" in messages[0]
    assert "card action 'detail'" in messages[0]


@pytest.mark.django_db
def test_stock_card_output_unchanged(cv_author, author_douglas_adams):
    client = _client(cv_author, ["view", "change", "delete"])
    doc = html.fromstring(client.get("/author/card/").content)
    actions = doc.cssselect(".card.mb-3")[0].cssselect("a.btn")
    assert "btn-secondary" in actions[1].get("class")
    assert "btn-outline-secondary" in actions[2].get("class")
