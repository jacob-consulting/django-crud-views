"""Phase 06.21 / #339: instance snippets see the view and, on a child ViewSet, the lazy parent object."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.test import RequestFactory

from tests.test1.app.models import Author
from tests.test1.app.views import AuthorPingView, BookCreateView


def _make_view(view_class, **url_kwargs):
    """A view instance set up for one GET request (as Django's as_view() would before dispatch)."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    view = view_class()
    view.setup(request, **url_kwargs)
    return view


def _publisher_queries(captured) -> list[str]:
    return [q["sql"] for q in captured.captured_queries if "app_publisher" in q["sql"]]


def _messages(response) -> list[str]:
    return [m.message for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
def test_e2e_create_header_renders_parent_object(client_user_book_add, publisher_penguin, monkeypatch):
    monkeypatch.setattr(BookCreateView, "cv_header_template_code", "New book for {{ parent_object }}")
    response = client_user_book_add.get(f"/publisher/{publisher_penguin.pk}/book/create/")
    assert response.status_code == 200
    assert f"New book for {publisher_penguin}" in response.content.decode()


@pytest.mark.django_db
def test_e2e_action_message_renders_view_attribute(client_user_author_change, monkeypatch):
    author = Author.objects.create(first_name="First", last_name="Author")

    def action(self, context):
        self.duplicate = "DRAFT-42"
        return True

    monkeypatch.setattr(AuthorPingView, "action", action)
    monkeypatch.setattr(AuthorPingView, "cv_message_template_code", "Created {{ view.duplicate }} from {{ object }}")
    response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    assert _messages(response) == [f"Created DRAFT-42 from {author}"]
