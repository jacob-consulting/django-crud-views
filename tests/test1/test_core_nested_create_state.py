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
