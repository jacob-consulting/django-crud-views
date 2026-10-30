"""AUTH-04 / WR-01: core create controls and direct requests share the URL parent's state.

These regressions deliberately retain the required behavior when production disagrees. No Guardian adapter is
involved: the registered core Book views expose the same public cv_action_enabled hook.
"""

from html.parser import HTMLParser

import pytest
from django.urls import reverse


class _Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hrefs = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href")


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["list", "detail"])
@pytest.mark.parametrize("enabled", [True, False], ids=["enabled-parent", "locked-parent"])
def test_core_nested_create_control_agrees_with_parent_state(client, monkeypatch, book_hitchhiker, page, enabled):
    from django.contrib.auth.models import User

    from tests.test1.app.models import Book, Publisher
    from tests.test1.app.views import BookCreateView, BookDetailView, BookListView, cv_book

    parent = book_hitchhiker.publisher
    calls = []

    @classmethod
    def parent_state(cls, user, obj=None):
        calls.append(obj)
        # A common consumer policy: child create is disabled only for a locked parent. Receiving the page Book
        # (or None on a list) must not accidentally turn a locked-parent create control into a live link.
        if isinstance(obj, Publisher):
            return enabled
        return not enabled

    monkeypatch.setattr(BookCreateView, "cv_action_enabled", parent_state)
    page_class = BookListView if page == "list" else BookDetailView
    monkeypatch.setattr(page_class, "cv_context_actions", ["create"])
    user = User.objects.create_superuser(username="core_parent_state", password="password")
    client.force_login(user)
    kwargs = {cv_book.parent.get_pk_name(): parent.pk}
    create_url = reverse(cv_book.get_router_name("create"), kwargs=kwargs)

    # First establish the request oracle with real GET and POST, independently of any rendering assertion.
    expected_status = 200 if enabled else 403
    assert client.get(create_url).status_code == expected_status
    title = "Core parent-state probe"
    assert client.post(create_url, {"title": title}).status_code == (302 if enabled else 403)
    assert list(Book.objects.filter(title=title).values_list("publisher_id", flat=True)) == (
        [parent.pk] if enabled else []
    )
    calls.clear()
    if page == "detail":
        kwargs["pk"] = book_hitchhiker.pk
    response = client.get(reverse(cv_book.get_router_name(page), kwargs=kwargs))
    assert response.status_code == 200
    hrefs = _Links(response.content.decode()).hrefs
    linked = any(href.split("?", 1)[0] == create_url for href in hrefs)
    observed = {"linked": linked, "state_objects": [type(obj).__name__ for obj in calls]}
    assert linked is enabled, f"{page} create control disagrees with direct GET/POST: {observed}"
    assert calls and all(isinstance(obj, Publisher) and obj.pk == parent.pk for obj in calls)


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["list", "detail"])
@pytest.mark.parametrize("enabled", [True, False])
def test_renamed_create_button_uses_url_parent(client, monkeypatch, book_hitchhiker, page, enabled):
    from crud_views.lib.view import ContextButton
    from tests.test1.app.views import BookCreateView, BookDetailView, BookListView, cv_book

    parent = book_hitchhiker.publisher
    calls = []
    monkeypatch.setattr(
        BookCreateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: calls.append(obj) or enabled)
    )
    page_class = BookListView if page == "list" else BookDetailView
    monkeypatch.setattr(page_class, "cv_context_buttons", [ContextButton(key="new_book", key_target="create")])
    view = _view(page_class, {cv_book.parent.get_pk_name(): parent.pk})
    obj = None if page == "list" else book_hitchhiker
    data = view.cv_get_context("new_book", obj=obj, user=view.request.user)
    assert data["cv_action_enabled"] is enabled
    assert data["cv_url"].split("?", 1)[0] == reverse(
        cv_book.get_router_name("create"), kwargs={cv_book.parent.get_pk_name(): parent.pk}
    )
    assert calls == [parent]


def _view(cls, kwargs=None):
    from types import SimpleNamespace

    from django.contrib.auth.models import AnonymousUser

    view = cls()
    view.request = SimpleNamespace(user=AnonymousUser(), GET={}, resolver_match=SimpleNamespace(url_name="test"))
    view.kwargs = kwargs or {}
    return view


@pytest.mark.django_db
@pytest.mark.parametrize("entry", ["card", "child-card", "child-button", "sibling-button"])
@pytest.mark.parametrize("enabled", [True, False])
def test_create_rendering_entry_points_keep_parent_and_adapter(monkeypatch, book_hitchhiker, entry, enabled):
    from crud_views.lib.view import CardAction, ChildContextButton, SiblingContextButton
    from crud_views.lib.views.card import CardListView
    from tests.test1.app.views import BookCreateView, BookListView, PublisherCardListView, cv_book

    parent = book_hitchhiker.publisher
    calls = []
    # An existing subclass adapter override must still receive the normalized state object.
    monkeypatch.setattr(
        BookCreateView,
        "_cv_action_enabled_for_context",
        classmethod(lambda cls, user, obj=None: calls.append(obj) or enabled),
    )
    if entry in {"child-card", "child-button"}:
        view = _view(PublisherCardListView)
        if entry == "child-card":
            data = view.cv_get_card_action_data(
                CardAction(child_name="book", child_key="create"), parent, view.request.user
            )
        else:
            data = ChildContextButton(key="new_book", child_name="book", child_key="create").get_context(
                view.cv_get_view_context(object=parent)
            )
    else:
        view = _view(BookListView, {cv_book.parent.get_pk_name(): parent.pk})
        if entry == "card":
            data = CardListView.cv_get_card_action_data(
                view, CardAction(key="create", label_mode="both"), book_hitchhiker, view.request.user
            )
        else:
            data = SiblingContextButton(key="new_book", sibling_name="book", sibling_key="create").get_context(
                view.cv_get_view_context(object=book_hitchhiker)
            )
    assert data["cv_action_enabled"] is enabled
    assert calls == [parent]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["parent", "child", "none", "unrelated", "missing-fk", "m2m-child"])
def test_core_create_adapter_normalizes_only_unambiguous_parent(monkeypatch, book_hitchhiker, kind):
    from tests.test1.app.models import Author, Book
    from tests.test1.app.views import BookCreateView, cv_book

    parent = book_hitchhiker.publisher
    calls = []
    monkeypatch.setattr(
        BookCreateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: calls.append(obj) or True)
    )
    obj = {
        "parent": parent,
        "child": book_hitchhiker,
        "none": None,
        "unrelated": Author(),
        "missing-fk": Book(),
        "m2m-child": book_hitchhiker,
    }[kind]
    if kind == "m2m-child":
        monkeypatch.setattr(cv_book.parent, "many_to_many_through_attribute", "books")
    expected = kind in {"parent", "child"}
    assert BookCreateView._cv_action_enabled_for_context(None, obj) is expected
    assert calls == ([parent] if expected else [])


@pytest.mark.django_db
def test_url_parent_wins_over_page_child_and_missing_parent_fails_closed(monkeypatch, book_hitchhiker, publisher_b):
    from tests.test1.app.views import BookCreateView, BookListView, cv_book

    calls = []
    monkeypatch.setattr(
        BookCreateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: calls.append(obj) or True)
    )
    view = _view(BookListView, {cv_book.parent.get_pk_name(): publisher_b.pk})
    assert view.cv_get_context("create", obj=book_hitchhiker, user=view.request.user)["cv_action_enabled"] is True
    assert calls == [publisher_b]
    calls.clear()
    view.kwargs[cv_book.parent.get_pk_name()] = 999999
    assert view.cv_get_context("create", obj=book_hitchhiker, user=view.request.user)["cv_action_enabled"] is False
    assert calls == []


@pytest.mark.django_db
def test_parent_button_top_level_create_keeps_existing_state_object(monkeypatch, book_hitchhiker):
    from crud_views.lib.view import ParentContextButton
    from tests.test1.app.views import BookListView, PublisherCreateView, cv_book, cv_publisher

    parent = book_hitchhiker.publisher
    calls = []
    monkeypatch.setattr(
        PublisherCreateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: calls.append(obj) or True)
    )
    view = _view(BookListView, {cv_book.parent.get_pk_name(): parent.pk})
    data = ParentContextButton(key="new_publisher", key_target="create").get_context(
        view.cv_get_view_context(object=book_hitchhiker)
    )
    assert data["cv_url"] == reverse(cv_publisher.get_router_name("create"))
    assert data["cv_action_enabled"] is True
    assert calls == [parent]


@pytest.mark.django_db
def test_m2m_create_uses_explicit_url_parent_without_inferring_from_child(monkeypatch, publisher_a, publisher_b):
    from tests.test1.app.models import Genre
    from tests.test1.app.views import GenreCreateView, GenreListView, cv_genre

    genre = Genre.objects.create(name="Two parents")
    publisher_a.genres.add(genre)
    publisher_b.genres.add(genre)
    calls = []
    monkeypatch.setattr(
        GenreCreateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: calls.append(obj) or True)
    )
    assert GenreCreateView._cv_action_enabled_for_context(None, genre) is False
    assert calls == []
    view = _view(GenreListView, {cv_genre.parent.get_pk_name(): publisher_b.pk})
    data = view.cv_get_context("create", obj=genre, user=view.request.user)
    assert data["cv_action_enabled"] is True
    assert calls == [publisher_b]
