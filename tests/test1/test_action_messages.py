import pytest
from django.contrib.messages import get_messages
from django.test.client import Client

from tests.test1.app.models import Author


def _messages(response) -> list[str]:
    return [m.message for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
def test_custom_form_view_emits_rendered_message(client_user_author_view: Client, cv_author):
    """MessageMixin form views still emit a message after the renderer moves to base."""
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_view.post(f"/author/{a.pk}/contact/", {"subject": "hi", "body": "there"})
    assert response.status_code == 302
    assert f"Contacted author »{a}«" in _messages(response)
