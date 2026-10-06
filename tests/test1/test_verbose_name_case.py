"""Verbose names are upper-cased on the first letter only (Django's capfirst), never lower-cased.

str.capitalize() lower-cases the rest: "S3-Dateien" -> "S3-dateien", "API key" -> "Api key".
"""

from types import SimpleNamespace

import pytest
from django.test.client import Client

from crud_views.lib.views.mixins import CardOrderMixin
from tests.test1.app.models import Author


@pytest.mark.django_db
def test_list_header_keeps_inner_capitals(client_user_author_view: Client, monkeypatch):
    monkeypatch.setattr(Author._meta, "verbose_name_plural", "API authors")
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "API authors" in content
    assert "Api authors" not in content


def test_order_field_label_keeps_inner_capitals(monkeypatch):
    monkeypatch.setattr(Author._meta.get_field("first_name"), "verbose_name", "ISO name")
    view = SimpleNamespace(model=Author)
    assert CardOrderMixin._order_field_label(view, "first_name") == "ISO name"
