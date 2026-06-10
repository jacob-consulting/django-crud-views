"""
Author has a UUID primary key. The URL regex must accept any UUID version,
not just version 4 (e.g. uuid1/uuid7 PKs created by the application).
"""

import uuid

import pytest
from django.test.client import Client

from tests.test1.app.models import Author


@pytest.mark.django_db
def test_detail_url_resolves_for_non_v4_uuid_pk(client_user_author_view: Client, cv_author):
    author = Author.objects.create(pk=uuid.uuid1(), first_name="Ursula", last_name="Le Guin")

    response = client_user_author_view.get(f"/author/{author.pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Ursula" in content


@pytest.mark.django_db
def test_detail_url_resolves_for_v4_uuid_pk(client_user_author_view: Client, cv_author, author_douglas_adams):
    response = client_user_author_view.get(f"/author/{author_douglas_adams.pk}/detail/")
    assert response.status_code == 200
